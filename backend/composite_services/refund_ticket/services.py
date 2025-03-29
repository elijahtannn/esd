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
        # Try multiple hostnames to improve reliability
        hosts_to_try = ['localhost', '127.0.0.1', 'host.docker.internal', 'rabbitmq']
        connected = False
        connection = None
        
        for host in hosts_to_try:
            try:
                logger.info(f"Attempting to connect to RabbitMQ at {host}:5672")
                credentials = pika.PlainCredentials('guest', 'guest')
                parameters = pika.ConnectionParameters(
                    host=host,
                    port=5672,
                    credentials=credentials,
                    connection_attempts=1,
                    socket_timeout=2,
                    blocked_connection_timeout=2
                )
                connection = pika.BlockingConnection(parameters)
                connected = True
                logger.info(f"Successfully connected to RabbitMQ at {host}")
                break
            except Exception as e:
                logger.warning(f"Failed to connect to RabbitMQ at {host}: {str(e)}")
                continue
        
        if not connected or not connection:
            logger.error("Failed to connect to RabbitMQ after trying all hosts")
            return False
        
        try:
            # Create channel
            channel = connection.channel()
            
            # Declare exchange
            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type='topic',
                durable=True
            )
            
            # Format notification message for the notification service
            notification = {
                "email": user_email,
                "eventType": event_type,
                "message": message,
                "ticketNumber": ticket_number or "",
                "amount": amount or 0,
                "eventName": event_name or "Ticket Refund"
            }
                    
            # Publish message
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=ROUTING_KEY,
                body=json.dumps(notification),
                properties=pika.BasicProperties(
                    delivery_mode=2  # Make message persistent
                )
            )
            
            # Close connection properly
            connection.close()
            logger.info(f"Successfully sent notification to {user_email}")
            return True
            
        except Exception as e:
            # Handle errors during messaging
            logger.error(f"Error sending message to RabbitMQ: {str(e)}")
            if connection and connection.is_open:
                try:
                    connection.close()
                except:
                    pass
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in notification service: {str(e)}")
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