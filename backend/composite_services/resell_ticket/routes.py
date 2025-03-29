from flask import Blueprint, request, jsonify
from services import update_ticket_status, update_event_inventory, get_ticket_details

resale_bp = Blueprint("resale_bp", __name__)

@resale_bp.route("/resale/list", methods=["POST"])
def list_resale_ticket():
    """List a single ticket for resale"""
    data = request.json
    required_fields = ["ticket_id", "cat_id", "resale_count"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    ticket_id = data["ticket_id"]
    cat_id = data["cat_id"]
    resale_count = int(data["resale_count"])

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
    inventory_response, inventory_status = update_event_inventory(cat_id, resale_count)
    if inventory_status != 200:
        return jsonify({"error": "Failed to update event inventory", "details": inventory_response}), inventory_status

    return jsonify({
        "message": "Ticket listed for resale successfully",
        "ticket_update": ticket_response,
        "inventory_update": inventory_response
    }), 200