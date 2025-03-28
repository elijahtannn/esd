from flask import Blueprint, request, jsonify
import logging
import requests
from config import Config
from services import (
    get_ticket_details,
    update_ticket_status,
    update_order_refund_status,
    get_order_via_user_endpoint,
    refund_payment,
    remove_ticket,
    send_transfer_notification
)

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
refund_bp = Blueprint('refund_bp', __name__)


@refund_bp.route("/refund", methods=["POST"])
def refund_user_ticket():
    """Process ticket refund after resale purchase"""
    data = request.json
    required_fields = ["ticket_id", "order_id", "user_id"]

    # Validate required fields
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Extract input data
    ticket_id = data["ticket_id"]
    order_id = data["order_id"]
    user_id = data["user_id"]  # This is the seller's user ID
    
    logger.info(f"Processing refund for ticket {ticket_id}, order {order_id}, user {user_id}")

    # Step 1: Get ticket details
    ticket_details, ticket_status = get_ticket_details(ticket_id)
    if ticket_status != 200:
        return jsonify({
            "error": "Failed to retrieve ticket details",
            "details": ticket_details
        }), ticket_status

    # Step 2: Validate ticket status - should be SOLD for a refund to proceed
    if ticket_details.get("status") != "sold":
        return jsonify({
            "error": f"Invalid ticket status: {ticket_details.get('status')}",
            "allowed_status": "sold"
        }), 400
    
    logger.info(f"Ticket {ticket_id} is in sold status, proceeding with refund")

    # Step 3: Get seller's order details
    seller_order, status = get_order_via_user_endpoint(user_id, order_id)
    if status != 200:
        return jsonify(seller_order), status
    
    # Step 4: Extract payment and price information
    try:
        # Get the original payment ID and amount
        payment_id = seller_order.get("paymentId")
        if not payment_id:
            return jsonify({"error": "Payment ID not found in order"}), 400

        # Find the appropriate refund amount
        # This depends on your data model - using a hypothetical approach here
        if "ticketPrices" in seller_order and ticket_id in seller_order["ticketPrices"]:
            refund_amount = seller_order["ticketPrices"][ticket_id]
        elif "totalPrice" in seller_order:
            # If multiple tickets, might need to divide by ticket count
            ticket_count = len(seller_order.get("ticketIds", []))
            if ticket_count > 0:
                refund_amount = float(seller_order["totalPrice"]) / ticket_count
            else:
                return jsonify({"error": "Cannot determine refund amount from order"}), 400
        else:
            return jsonify({"error": "Price information not found in order"}), 400
            
        refund_amount = round(float(refund_amount), 2)
        if refund_amount <= 0:
            return jsonify({"error": "Refund amount must be positive"}), 400
            
        logger.info(f"Calculated refund amount: ${refund_amount:.2f}")
        
    except (ValueError, KeyError) as e:
        logger.error(f"Error extracting payment details: {str(e)}")
        return jsonify({
            "error": f"Failed to extract payment details: {str(e)}",
            "order_keys": list(seller_order.keys())
        }), 400

    # Step 5: Process payment refund
    logger.info(f"Processing refund of ${refund_amount:.2f} for payment {payment_id}")
    refund_response, refund_status = refund_payment(payment_id, refund_amount)
    if refund_status != 200:
        return jsonify(refund_response), refund_status

    refund_id = refund_response.get("refund_id")
    if not refund_id:
        return jsonify({
            "error": "Payment service returned invalid refund ID",
            "response": refund_response
        }), 500
    
    logger.info(f"Refund processed successfully with ID {refund_id}")

    # Step 6: Update ticket status to REFUNDED
    logger.info(f"Updating ticket {ticket_id} status to REFUNDED")
    ticket_update, ticket_update_status = update_ticket_status(ticket_id, "REFUNDED")
    if ticket_update_status != 200:
        # Attempt refund rollback
        logger.error(f"Failed to update ticket status: {ticket_update}")
        requests.delete(f"{Config.PAYMENT_SERVICE_URL}/payments/refund/{refund_id}")
        return jsonify({
            "error": "Ticket status update failed",
            "details": ticket_update,
            "refund_id": refund_id  # For manual reconciliation
        }), ticket_update_status

    # Step 7: Update SELLER's order with refund details
    logger.info(f"Updating seller order {order_id} with refund details")
    order_update, order_update_status = update_order_refund_status(
        order_id=order_id,
        ticket_id=ticket_id,
        refund_amount=refund_amount,
        refund_id=refund_id
    )
    if order_update_status != 200:
        # Rollback both operations
        logger.error(f"Failed to update order: {order_update}")
        requests.delete(f"{Config.PAYMENT_SERVICE_URL}/payments/refund/{refund_id}")
        update_ticket_status(ticket_id, "sold")
        return jsonify({
            "error": "Order update failed",
            "details": order_update,
            "rollback_performed": True
        }), order_update_status
   
    # Step 8: Send notifications
    # Assuming seller_id is the same as user_id in this context
    seller_id = user_id
    
    # Find buyer ID from ticket details if available
    buyer_id = ticket_details.get("owner_id") or "Unknown"
    
    logger.info(f"Sending notifications to seller {seller_id}")
    seller_notification_sent = send_transfer_notification(
        user_email=seller_id,
        message=f"Your refund of ${refund_amount:.2f} for ticket {ticket_id} has been processed",
        event_type="refund.seller.complete"
    )

    return jsonify({
        "message": "Refund to seller processed successfully",
        "refund_id": refund_id,
        "ticket_status": "REFUNDED",
        "order_status": "REFUNDED",
        "amount_refunded": refund_amount,
        "notification_sent": seller_notification_sent
    }), 200


@refund_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "service": "refund_user"}), 200