import requests
import json
import pika
import logging
import os
from datetime import datetime

# RabbitMQ Configuration
EXCHANGE_NAME = "ticketing.exchange"
ROUTING_KEY = "ticket.refund.complete"

# Service URLs (for use in this file)
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://127.0.0.1:8002")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_transfer_notification(user_email, message, event_type, ticket_number=None, amount=None, event_name=None):
    """Send notification via RabbitMQ with improved connection handling"""
    try:
        # Log notification details
        notification = {
            "email": user_email,
            "eventType": event_type,
            "message": message,
            "ticketNumber": ticket_number or "",
            "amount": amount or 0,
            "eventName": event_name or "Ticket Refund"
        }
        logger.info(f"Attempting to send notification with routing key: {ROUTING_KEY}")
        logger.info(f"Notification payload: {json.dumps(notification)}")
        
        parameters = pika.URLParameters(os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672"))
        parameters.connection_attempts = 1
        parameters.socket_timeout = 2
        
        connection = pika.BlockingConnection(parameters)
        logger.info("Successfully connected to RabbitMQ")
        
        try:
            # Create channel
            channel = connection.channel()
            logger.info("Created RabbitMQ channel")
            
            # Declare exchange
            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type='topic',
                durable=True
            )
            logger.info(f"Declared exchange: {EXCHANGE_NAME}")
            
            # Publish message
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=ROUTING_KEY,
                body=json.dumps(notification),
                properties=pika.BasicProperties(
                    delivery_mode=2
                )
            )
            logger.info("Message published successfully")
            
            connection.close()
            logger.info(f"Successfully sent notification to {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to RabbitMQ: {str(e)}")
            if connection and connection.is_open:
                connection.close()
            return False
            
    except Exception as e:
        logger.error(f"Could not connect to RabbitMQ: {str(e)}")
        return False

def refund_payment(payment_id, amount):
    """Process payment refund through Payment Service"""
    url = f"{PAYMENT_SERVICE_URL}/payments/refund"
    payload = {
        "payment_id": payment_id,
        "amount": amount
    }
    try:
        logger.info(f"Sending refund request to Payment Service: {payload}")
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code != 200:
            logger.error(f"Payment service error: {response.text}")
            return {"error": response.text}, response.status_code
        
        result = response.json()
        logger.info(f"Refund processed successfully: {result}")
        return result, response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Payment service connection error: {str(e)}")
        return {"error": f"Payment service unavailable: {str(e)}"}, 503