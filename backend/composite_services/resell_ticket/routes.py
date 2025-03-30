from flask import Blueprint, request, jsonify
from services import (
    update_ticket_status, 
    update_event_inventory, 
    get_ticket_details, 
    get_event_details,
    get_category_details
)
from rabbit_publisher import RabbitMQPublisher

resale_bp = Blueprint("resale_bp", __name__)
rabbitmq_publisher = RabbitMQPublisher()

@resale_bp.route("/resale/list", methods=["POST"])
def list_resale_ticket():
    """List a single ticket for resale"""
    data = request.json
    required_fields = ["ticket_id", "cat_id"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    ticket_id = data["ticket_id"]
    cat_id = data["cat_id"]
    
    # Optional: Get event_id from request if available, otherwise we'll get it from ticket details
    event_id = data.get("event_id")

    # Step 1: Get the current ticket details from Ticket Service
    ticket_details, ticket_status = get_ticket_details(ticket_id)

    if ticket_status != 200:
        return jsonify({"error": "Failed to retrieve ticket details", "details": ticket_details}), ticket_status

    current_status = ticket_details.get("status")
    
    # Get event_id from ticket details if not provided in request
    if not event_id and "event_id" in ticket_details:
        event_id = ticket_details["event_id"]

    # Step 2: Validate ticket status before allowing resale
    if current_status not in ["SOLD", "TRANSFERRED", "sold", "transferred"]:
        return jsonify({
            "error": f"Ticket cannot be listed for resale. Current status: {current_status}"
        }), 400
    
    # Step 3: Update event inventory in OutSystems Event Service
    inventory_response, inventory_status = update_event_inventory(cat_id, 1)
    
    # Check for errors in the inventory response
    if inventory_status != 200 or (isinstance(inventory_response, dict) and 
                                  inventory_response.get("Result") and 
                                  "ErrorMessage" in inventory_response["Result"]):
        error_message = inventory_response.get("Result", {}).get("ErrorMessage", "Unknown error")
        return jsonify({"error": "Failed to update event inventory", "details": error_message}), 400
    
    # Step 4: Only update ticket status if inventory update was successful
    ticket_response, ticket_status = update_ticket_status(ticket_id)
    if ticket_status != 200:
        return jsonify({"error": "Failed to update ticket status", "details": ticket_response}), ticket_status

    # Step 5: Gather event information for notification
    event_name = None
    event_details = {}
    
    # Try to get category details first
    category_details, category_status = get_category_details(cat_id)
    if category_status == 200 and "Result" in category_details:
        if isinstance(category_details["Result"], dict):
            # Extract event details from category
            event_details["categoryName"] = category_details["Result"].get("Name")
            event_details["ticketPrice"] = category_details["Result"].get("Price")
            
            # If we have event_id, get more details
            if not event_id and "EventId" in category_details["Result"]:
                event_id = category_details["Result"]["EventId"]
    
    # If we have event_id, get event details
    if event_id:
        event_info, event_status = get_event_details(event_id)
        if event_status == 200 and "Result" in event_info:
            if isinstance(event_info["Result"], dict):
                event_name = event_info["Result"].get("Name", "Event")
                
                # Add more details for notification
                event_details["eventDate"] = event_info["Result"].get("Date")
                event_details["eventLocation"] = event_info["Result"].get("Location")
                event_details["eventVenue"] = event_info["Result"].get("Venue")
    
    # If we couldn't get event name, use a default
    if not event_name:
        event_name = ticket_details.get("event_name", "Event")
    
    # Set ticket quantity to 1 since this is for a single ticket
    event_details["ticketQuantity"] = 1
    
    # Step 6: Publish message to notify interested users
    if event_id:
        # Try to publish notification
        notification_sent = rabbitmq_publisher.publish_resale_availability(
            event_id=event_id,
            event_name=event_name,
            ticket_details=event_details
        )
        
        # Add notification status to response
        ticket_response["notification_sent"] = notification_sent
    
    return jsonify({
        "message": "Ticket listed for resale successfully",
        "ticket_update": ticket_response,
        "inventory_update": inventory_response
    }), 200