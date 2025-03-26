from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

load_dotenv()
# Service URLs
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://127.0.0.1:5001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8003")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://127.0.0.1:8002")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_ticket_details(ticket_id):
    """Fetch ticket details from Ticket Service"""
    url = f"{TICKET_SERVICE_URL}/tickets/{ticket_id}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json(), 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Ticket service error: {str(e)}")
        return {"error": f"Ticket service unavailable: {str(e)}"}, 503
    except ValueError:
        return {"error": "Invalid ticket data format"}, 500

def update_order_refund_status(order_id, ticket_id, refund_amount, refund_id=None):
    """Update order status with refund details"""
    url = f"{ORDER_SERVICE_URL}/orders/{order_id}"
    payload = {
        "status": "REFUNDED",
        "refundDetails": {
            "ticketId": ticket_id,
            "amount": refund_amount,
            "timestamp": datetime.utcnow().isoformat(),
            **({"refundId": refund_id} if refund_id else {})
        }
    }
    try:
        response = requests.put(url, json=payload, timeout=5)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Order service update error: {str(e)}")
        return {"error": f"Order service unavailable: {str(e)}"}, 503

def update_ticket_status(ticket_id, new_status):
    """Update ticket status in Ticket Service"""
    url = f"{TICKET_SERVICE_URL}/tickets/{ticket_id}"
    payload = {"status": new_status}
    try:
        response = requests.put(url, json=payload, timeout=5)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Ticket status update error: {str(e)}")
        return {"error": f"Ticket service unavailable: {str(e)}"}, 503

def get_order_via_user_endpoint(user_id, target_order_id):
    """Get specific order from user's order list"""
    url = f"{ORDER_SERVICE_URL}/orders/user/{user_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None, response.status_code
        
        orders = response.json()
        if not isinstance(orders, list):
            return {"error": "Invalid orders data format"}, 500
            
        target_order = next(
            (o for o in orders if str(o.get("orderId")) == str(target_order_id)),
            None
        )
        return (target_order, 200) if target_order else ({"error": "Order not found"}, 404)
    except requests.exceptions.RequestException as e:
        logger.error(f"Order service error: {str(e)}")
        return {"error": f"Order service unavailable: {str(e)}"}, 503

def refund_payment(payment_id, amount):
    """Process payment refund through Payment Service"""
    url = f"{PAYMENT_SERVICE_URL}/payments/refund"
    payload = {
        "payment_id": payment_id,
        "amount": amount
    }
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code != 200:
            logger.error(f"Payment service error: {response.text}")
            return {"error": response.text}, response.status_code
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Payment service connection error: {str(e)}")
        return {"error": f"Payment service unavailable: {str(e)}"}, 503
    
def remove_ticket(order_id, ticket_id):
    """Fallback for services that don't support operators"""
    # 1. Get full order
    order = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}").json()
    
    # 2. Modify locally
    if ticket_id in order["ticketIds"]:
        order["ticketIds"].remove(ticket_id)
    else:
        return {"error": "Ticket not in order"}, 404
    
    # 3. Full document update
    response = requests.put(
        f"{ORDER_SERVICE_URL}/orders/{order_id}",
        json=order  # Send entire modified document
    )
    return response.json(), response.status_code


@app.route("/refund", methods=["POST"])
def refund_user_ticket():
    """Process ticket refund end-to-end"""
    data = request.json
    required_fields = ["ticket_id", "order_id", "refund_amount", "user_id"]
    
    # Validate required fields
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Extract and validate input data
    ticket_id = data["ticket_id"]
    order_id = data["order_id"]
    user_id = data["user_id"]
    try:
        refund_amount = round(float(data["refund_amount"]), 2)
        if refund_amount <= 0:
            return jsonify({"error": "Refund amount must be positive"}), 400
    except ValueError:
        return jsonify({"error": "Invalid refund amount format"}), 400

    # Step 1: Get order details
    order_data, status = get_order_via_user_endpoint(user_id, order_id)
    if status != 200:
        return jsonify(order_data), status

    # Step 2: Validate payment reference
    try:
        payment_id = order_data["paymentId"]
        seller_id = order_data["userId"]
    except KeyError as e:
        logger.error(f"Missing order field: {str(e)}")
        return jsonify({
            "error": f"Order missing critical field: {str(e)}",
            "order_keys": list(order_data.keys())
        }), 400

    # Step 3: Get ticket details
    ticket_details, ticket_status = get_ticket_details(ticket_id)
    if ticket_status != 200:
        return jsonify({
            "error": "Failed to retrieve ticket details",
            "details": ticket_details
        }), ticket_status

    # Step 4: Validate ticket status
    if ticket_details.get("status") != "RESALE":
        return jsonify({
            "error": f"Invalid ticket status: {ticket_details.get('status')}",
            "allowed_status": "RESALE"
        }), 400

    # Step 5: Process payment refund
    refund_response, refund_status = refund_payment(payment_id, refund_amount)
    if refund_status != 200:
        return jsonify(refund_response), refund_status

    refund_id = refund_response.get("refund_id")
    if not refund_id:
        return jsonify({
            "error": "Payment service returned invalid refund ID",
            "response": refund_response
        }), 500

    # Step 6: Update ticket status
    ticket_update, ticket_update_status = update_ticket_status(ticket_id, "REFUNDED")
    if ticket_update_status != 200:
        # Attempt refund rollback
        requests.delete(f"{PAYMENT_SERVICE_URL}/payments/refund/{refund_id}")
        return jsonify({
            "error": "Ticket status update failed",
            "details": ticket_update,
            "refund_id": refund_id  # For manual reconciliation
        }), ticket_update_status

    # Step 7: Update order status
    order_update, order_update_status = update_order_refund_status(
        order_id=order_id,
        ticket_id=ticket_id,
        refund_amount=refund_amount,
        refund_id=refund_id
    )
    if order_update_status != 200:
        # Rollback both operations
        requests.delete(f"{PAYMENT_SERVICE_URL}/payments/refund/{refund_id}")
        update_ticket_status(ticket_id, "RESALE")
        return jsonify({
            "error": "Order update failed",
            "details": order_update,
            "rollback_performed": True
        }), order_update_status

    return jsonify({
        "message": "Refund processed successfully",
        "refund_id": refund_id,
        "ticket_status": "REFUNDED",
        "order_status": "REFUNDED",
        "amount_refunded": refund_amount
    }), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5004)
