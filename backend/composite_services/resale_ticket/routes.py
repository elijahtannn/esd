from flask import Blueprint, request, jsonify
import requests
from services import (
    update_ticket_status, 
    update_event_inventory, 
    get_ticket_details, 
    get_interested_users,
    publish_notification,
    get_event_id_by_category
)

resale_bp = Blueprint("resale_bp", __name__)

@resale_bp.route("/resale/list", methods=["POST"])
def list_resale_ticket():
    """List a single ticket for resale"""
    data = request.json
    required_fields = ["ticket_id", "cat_id"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    ticket_id = data["ticket_id"]
    cat_id = data["cat_id"]

    # Step 1: Get the current ticket details from Ticket Service
    ticket_details, ticket_status = get_ticket_details(ticket_id)

    if ticket_status != 200:
        return jsonify({"error": "Failed to retrieve ticket details", "details": ticket_details}), ticket_status

    current_status = ticket_details.get("status")

    # Step 2: Validate ticket status before allowing resale
    if current_status not in ["SOLD", "TRANSFERRED"]:
        return jsonify({
            "error": f"Ticket cannot be listed for resale. Current status: {current_status}"
        }), 400
    
    # Step 3: Update ticket status in Ticket Service
    ticket_response, ticket_status = update_ticket_status(ticket_id)
    if ticket_status != 200:
        return jsonify({"error": "Failed to update ticket status", "details": ticket_response}), ticket_status

    # Step 4: Update event inventory in OutSystems Event Service
    inventory_response, inventory_status = update_event_inventory(cat_id, 1)
    if inventory_status != 200:
        return jsonify({"error": "Failed to update event inventory", "details": inventory_response}), inventory_status
    
    # Step 5: Fetch event ID
    event_id_response, event_id_status = get_event_id_by_category(cat_id)

    if event_id_status != 200:
        return jsonify({
            "error": "Failed to retrieve event ID",
            "details": event_id_response
        }), event_id_status
    
    event_id = event_id_response

    # Step 6: Fetch interested users
    interested_users_response, interested_users_status = get_interested_users(event_id)
    
    # Prepare notification results
    notification_results = []
    
    # If interested users are found, publish notifications
    if interested_users_status == 200:
        interested_users = interested_users_response.get('users', [])
        
        for user in interested_users:
            # Prepare notification payload
            notification_payload = {
                "email": user['email'],
                "eventType": "ticket.resale.available",
                "eventName": ticket_details.get('event_name', 'Event'),
                "eventId": event_id,
                "venue": ticket_details.get('venue', 'Not specified'),
                "eventDate": ticket_details.get('event_date', 'Not specified'),
                "ticketNumber": ticket_id
            }
            
            # Publish notification
            notification_response, notification_status = publish_notification(notification_payload)
            
            # Track notification results
            notification_results.append({
                "user_id": user['id'],
                "email": user['email'],
                "status": "success" if notification_status == 200 else "failed",
                "details": notification_response
            })
    else:
        # Log error if fetching interested users fails
        interested_users = []

    return jsonify({
        "message": "Ticket listed for resale successfully",
        "ticket_update": ticket_response,
        "inventory_update": inventory_response,
        "notifications": {
            "total_users": len(interested_users),
            "results": notification_results
        }
    }), 200