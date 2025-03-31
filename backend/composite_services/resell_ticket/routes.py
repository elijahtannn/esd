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
print(f"Initialized RabbitMQ publisher with URL: {rabbitmq_publisher.rabbitmq_url}")

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
    print(f"DEBUG: Starting to gather event details for event_id: {event_id}")
    event_name = None
    event_details = {}

    # If we have event_id, get event details
    if event_id:
        event_info, event_status = get_event_details(event_id)
        print(f"DEBUG: Event details status: {event_status}")
        print(f"DEBUG: Full event response: {event_info}")

        # Check if the request was successful
        if event_status == 200:
            # The response now has "Event" key instead of "Events"
            events_data = event_info.get("Event", [])
            
            if events_data:
                # Prefer events with matching EventId or Id
                matched_event = next((event for event in events_data 
                                      if str(event.get("EventId")) == str(event_id) or 
                                         str(event.get("Id")) == str(event_id)), 
                                     events_data[0])
                
                # Extract event details
                event_name = matched_event.get("Name", "Event")
                event_details = {
                    "eventId": event_id,
                    "eventName": event_name,
                    "eventDate": matched_event.get("Date", ""),
                    "eventLocation": matched_event.get("Venue", ""),
                    "eventVenue": matched_event.get("Venue", ""),
                    "categoryName": matched_event.get("Category", ""),
                }
                
                print(f"DEBUG: Extracted Event Details: {event_details}")
            else:
                print("DEBUG: No events found in the response")
        else:
            print(f"DEBUG: Failed to retrieve event details. Status: {event_status}")
            print(f"DEBUG: Response: {event_info}")
    
    # Step 6: Publish message to notify interested users
    if event_id and event_details:
        print(f"DEBUG: Publishing notification for event {event_id}")
        print(f"DEBUG: RabbitMQ URL: {rabbitmq_publisher.rabbitmq_url}")
        
        # Try to publish notification
        notification_sent = rabbitmq_publisher.publish_resale_availability(
            event_id=event_id,
            event_name=event_details.get("eventName"),
            ticket_details=event_details
        )
        
        print(f"DEBUG: Notification published: {notification_sent}")
        
        # Add notification status to response
        ticket_response["notification_sent"] = notification_sent
    else:
        print("DEBUG: Cannot publish notification - missing event ID or details")
        ticket_response["notification_sent"] = False
    
    return jsonify({
        "message": "Ticket listed for resale successfully",
        "ticket_update": ticket_response,
        "inventory_update": inventory_response
    }), 200