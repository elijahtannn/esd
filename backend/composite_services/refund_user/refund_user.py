from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import logging
import pika
import json








app = Flask(__name__)
CORS(app)




load_dotenv()
# Service URLs
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://127.0.0.1:5001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8003")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://127.0.0.1:8002")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5003")




EXCHANGE_NAME = "refund.exchange"
ROUTING_KEY = "refund.user.complete"




def send_transfer_notification(user_email, message, event_type):
    try:
        # For local RabbitMQ, use host.docker.internal since service is in container
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host='host.docker.internal',  # This allows container to access local RabbitMQ
            port=5672,  
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()




        # Declare exchange
        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type='topic',
            durable=True
        )




        # Prepare message
        message = {
            "eventType": "refund.user.complete",
            "email": user_email,
            "eventType": event_type,
            "message": message
        }




        # Publish message
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  
            )
        )




        connection.close()
        return True
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False


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


def remove_ticket(user_id, order_id, ticket_id):
    """Remove a ticket from an order using /orders/user/{user_id}"""
    # Fetch all orders for the user
    response = requests.get(f"{ORDER_SERVICE_URL}/orders/user/{user_id}")
    if response.status_code != 200:
        return {"error": f"Failed to fetch orders: {response.status_code}"}, response.status_code

    try:
        orders = response.json()  # Extract JSON safely
    except requests.exceptions.JSONDecodeError:
        return {"error": "Invalid JSON response from server"}, 500

    # Find the specific order by order_id
    target_order = next((order for order in orders if str(order.get("orderId")) == str(order_id)), None)
    if not target_order:
        return {"error": "Order not found"}, 404

    # Validate and modify the ticket list in the order
    if "ticketIds" not in target_order or not isinstance(target_order["ticketIds"], list):
        return {"error": "Invalid order format"}, 400

    if ticket_id not in target_order["ticketIds"]:
        return {"error": "Ticket not found in order"}, 404

    # Remove the ticket from the list
    target_order["ticketIds"].remove(ticket_id)

    # Update the modified order using PUT
    update_response = requests.put(
        f"{ORDER_SERVICE_URL}/orders/{order_id}",
        json=target_order,
        headers={"Content-Type": "application/json"}
    )

    if update_response.status_code != 200:
        return {"error": f"Failed to update order: {update_response.status_code}"}, update_response.status_code

    return update_response.json(), update_response.status_code



def validate_recipient(email):
    try:
        response = requests.get(f"{USER_SERVICE_URL}/user/email/{email}")
        is_valid = response.status_code == 200
        messages = ["Recipient email is valid"] if is_valid else ["Recipient email not found"]
        return {
            "is_valid": is_valid,
            "messages": messages
        }




    except Exception as e:
        return {
            "is_valid": False,
            "messages": [f"Error validating recipient: {str(e)}"]
        }




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




    # Step 4: Remove ticket from order
    remove_ticket_response, remove_ticket_status = remove_ticket(user_id, order_id, ticket_id)
    if remove_ticket_status != 200:
        return jsonify({
            "error": "Failed to remove ticket from order",
            "details": remove_ticket_response
        }), remove_ticket_status




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
   
    # After successful refund process
    user_notification_sent = send_transfer_notification(
        sender_email="pritika.kashyap.19@gmail.com",
        user_email=user_id,
        message=f"Your refund of {refund_amount} for ticket {ticket_id} has been processed",
        event_type="refund.user.complete"
    )




    seller_notification_sent = send_transfer_notification(
        sender_email="pritika.kashyap.19@gmail.com",
        user_email=seller_id,
        message=f"A refund of {refund_amount} for ticket {ticket_id} has been processed",
        event_type="refund.seller.complete"
    )








    return jsonify({
        "message": "Refund processed successfully",
        "refund_id": refund_id,
        "ticket_status": "REFUNDED",
        "order_status": "REFUNDED",
        "amount_refunded": refund_amount,
        "notifications_sent": user_notification_sent and seller_notification_sent




    }), 200




if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5004)
