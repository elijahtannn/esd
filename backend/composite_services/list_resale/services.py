import requests
from config import Config
import json
import pika

def get_ticket_details(ticket_id):
    """Fetch ticket details from Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"

    response = requests.get(url)

    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from Ticket Service"}

    return response_data, response.status_code

def update_ticket_status(ticket_id):
    """Update ticket status to 'RESALE' in Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"
    payload = {"status": "RESALE"}
    
    response = requests.put(url, json=payload)
    return response.json(), response.status_code

def update_event_inventory(cat_id, resale_count):
    """Update event inventory in OutSystems Event Service"""
    url = f"{Config.OUTSYSTEMS_EVENT_API_URL}/events/dates/categories/{cat_id}/inventory/resale"
    
    headers = {
        "Content-Type": "application/json",
    }

    payload = {"Count": resale_count}

    response = requests.put(url, json=payload, headers=headers)
    
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from OutSystems"}

    return response_data, response.status_code

def get_event_id_by_category(cat_id):
    """
    Retrieve event ID using category ID from OutSystems Event Service
    
    Args:
        cat_id (str): Category ID
    
    Returns:
        tuple: (event_id, status_code)
    """
    url = f"{Config.OUTSYSTEMS_EVENT_API_URL}/events/categories/{cat_id}/eventId"
    
    try:
        response = requests.get(url)
        
        try:
            response_data = response.json()
            
            # Check the response structure based on the example
            if response_data.get('Success') is False:
                return {
                    "error": response_data.get('ErrorMessage', 'Unknown error'),
                    "category_id": cat_id
                }, 400
            
            event_id = response_data.get('EventId')
            
            if event_id:
                return event_id, 200
            else:
                return {
                    "error": "Event ID not found for the given category",
                    "category_id": cat_id
                }, 404
        
        except ValueError:
            return {
                "error": "Invalid JSON response from OutSystems Event Service"
            }, 500
    
    except requests.RequestException as e:
        return {
            "error": "Failed to connect to OutSystems Event Service",
            "details": str(e)
        }, 500

def get_interested_users(event_id):
    url = f"{Config.USER_SERVICE_URL}/user/interested_users/{event_id}"
    
    try:
        response = requests.get(url)
        
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"error": "Invalid JSON response from User Service"}
        
        return response_data, response.status_code
    
    except requests.RequestException as e:
        return {
            "error": "Failed to connect to User Service",
            "details": str(e)
        }, 500


def publish_notification(notification_payload):
    """
    Publish a notification to RabbitMQ
    
    Args:
        notification_payload (dict): Notification details to be published
    
    Returns:
        tuple: (response_data, status_code)
    """
    try:
        # RabbitMQ connection parameters
        connection_params = pika.ConnectionParameters(
            host='localhost',  # Use localhost for local RabbitMQ
            port=5672,          # Default RabbitMQ port
            credentials=pika.PlainCredentials('guest', 'guest')  # Default credentials
        )

        # Establish connection
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        # Declare the exchange (same as in notification service)
        exchange_name = 'ticketing.exchange'
        routing_key = 'ticket.resale.available'  # Specific routing key for resale

        # Publish the message
        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(notification_payload),
            properties=pika.BasicProperties(
                content_type='application/json'
            )
        )

        # Close the connection
        connection.close()

        return {"message": "Notification published successfully"}, 200

    except Exception as e:
        return {
            "error": "Failed to publish notification",
            "details": str(e)
        }, 500