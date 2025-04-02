from flask import Blueprint, request, jsonify
from services import (
    update_ticket_status, 
    update_event_inventory, 
    get_ticket_details, 
    get_event_details,
    get_category_details,
    get_interested_users
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

    # Step 5: Gather event information and notify interested users
    print(f"DEBUG: Starting to gather event details for event_id: {event_id}")
    event_name = None
    event_details = {}

    if event_id:
        event_info, event_status = get_event_details(event_id)
        print(f"DEBUG: Event details status: {event_status}")
        print(f"DEBUG: Full event response: {event_info}")

        if event_status == 200:
            events_data = event_info.get("Event", [])
            
            if events_data:
                matched_event = next((event for event in events_data 
                                    if str(event.get("EventId")) == str(event_id) or 
                                       str(event.get("Id")) == str(event_id)), 
                                   events_data[0])
                
                event_name = matched_event.get("Name", "Event")
                event_details = {
                    "eventId": event_id,
                    "eventName": event_name,
                    "eventDate": matched_event.get("Date", ""),
                    "eventLocation": matched_event.get("Venue", ""),
                    "eventVenue": matched_event.get("Venue", ""),
                    "categoryName": matched_event.get("Category", ""),
                }
                
                # Get interested users and send notifications
                interested_users, users_status = get_interested_users(event_id)
                if users_status == 200 and interested_users:
                    # Publish notification for each interested user
                    for user in interested_users:
                        notification_data = {
                            "eventType": "ticket.resale.available",
                            "email": user["email"],
                            "eventId": event_id,
                            "eventName": event_name,
                            **event_details
                        }
                        rabbitmq_publisher.publish_message(
                            routing_key="ticket.resale.available",
                            message=notification_data
                        )
                        print(f"DEBUG: Notification sent to user {user['email']}")
            else:
                print("DEBUG: No events found in the response")
        else:
            print(f"DEBUG: Failed to retrieve event details. Status: {event_status}")
            print(f"DEBUG: Response: {event_info}")
    
    return jsonify({
        "message": "Ticket listed for resale successfully",
        "ticket_update": ticket_response,
        "inventory_update": inventory_response
    }), 200