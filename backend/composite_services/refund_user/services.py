import requests
from config import Config
from datetime import datetime
import pika
import json
import logging

logger = logging.getLogger(__name__)

def get_ticket_details(ticket_id):
    """Fetch ticket details from Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"
    response = requests.get(url)
    
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from Ticket Service"}
    
    return response_data, response.status_code


def update_ticket_status(ticket_id, status="REFUNDED"):
    """Update ticket status in Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"
    payload = {"status": status}
    
    response = requests.put(url, json=payload)
    return response.json(), response.status_code


def update_order_refund_status(order_id, ticket_id, refund_amount, refund_id=None):
    """Update order status with refund details"""
    url = f"{Config.ORDER_SERVICE_URL}/orders/{order_id}"
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


def get_order_via_user_endpoint(user_id, target_order_id):
    """Get specific order from user's order list"""
    url = f"{Config.ORDER_SERVICE_URL}/orders/user/{user_id}"
    
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
    url = f"{Config.PAYMENT_SERVICE_URL}/payments/refund"
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
    response = requests.get(f"{Config.ORDER_SERVICE_URL}/orders/user/{user_id}")
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
        f"{Config.ORDER_SERVICE_URL}/orders/{order_id}",
        json=target_order,
        headers={"Content-Type": "application/json"}
    )

    if update_response.status_code != 200:
        return {"error": f"Failed to update order: {update_response.status_code}"}, update_response.status_code

    return update_response.json(), update_response.status_code


def send_transfer_notification(user_email, message, event_type):
    """Send notification via RabbitMQ"""
    try:
        # RabbitMQ connection
        credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=Config.RABBITMQ_HOST,
            port=Config.RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare exchange
        channel.exchange_declare(
            exchange=Config.EXCHANGE_NAME,
            exchange_type='topic',
            durable=True
        )

        # Prepare message
        notification = {
            "eventType": event_type,
            "email": user_email,
            "message": message
        }

        # Publish message
        channel.basic_publish(
            exchange=Config.EXCHANGE_NAME,
            routing_key=Config.ROUTING_KEY,
            body=json.dumps(notification),
            properties=pika.BasicProperties(
                delivery_mode=2  # persistent message
            )
        )

        connection.close()
        return True
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False