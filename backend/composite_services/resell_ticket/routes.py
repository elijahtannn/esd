from flask import Blueprint, request, jsonify
from services import update_ticket_status, update_event_inventory, get_ticket_details

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

    return jsonify({
        "message": "Ticket listed for resale successfully",
        "ticket_update": ticket_response,
        "inventory_update": inventory_response
    }), 200