from flask import Blueprint, request, jsonify
from services import get_ticket_details, update_order_refund_status, refund_payment, update_ticket_status

refund_bp = Blueprint("refund_bp", __name__)

@refund_bp.route("/refund", methods=["POST"])

def refund_user_ticket():
    """Refund a user's ticket"""
    data = request.json
    required_fields = ["ticket_id", "order_id", "seller_id", "refund_amount"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    ticket_id = data["ticket_id"]
    order_id = data["order_id"]
    seller_id = data["seller_id"]
    refund_amount = float(data["refund_amount"])

    # Step 1: Get the current ticket details from Ticket Service
    ticket_details, ticket_status = get_ticket_details(ticket_id)

    if ticket_status != 200:
        return jsonify({"error": "Failed to retrieve ticket details", "details": ticket_details}), ticket_status

    current_status = ticket_details.get("status")

    # Step 2: Validate ticket status before allowing refund
    if current_status != "sold":
        return jsonify({
            "error": f"Ticket cannot be refunded. Current status: {current_status}"
        }), 400
    
    # Step 3: Update ticket status in Ticket Service
    refund_response, refund_status = refund_payment(seller_id, refund_amount)
    if refund_status != 200:
        return jsonify({"error": "Failed to process refund", "details": refund_response}), refund_status

        # Step 4: Update ticket status in Ticket Service
    ticket_response, ticket_status = update_ticket_status(ticket_id, "REFUNDED")
    if ticket_status != 200:
        return jsonify({"error": "Failed to update ticket status", "details": ticket_response}), ticket_status

    # Step 5: Update order with refund details
    order_response, order_status = update_order_refund_status(order_id, seller_id, ticket_id)
    if order_status != 200:
        return jsonify({"error": "Failed to update order status", "details": order_response}), order_status

    return jsonify({
        "message": "Ticket refunded successfully",
        "ticket_update": ticket_response,
        "refund_details": refund_response,
        "order_update": order_response
    }), 200
