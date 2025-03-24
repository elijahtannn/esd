from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import pika
import json

app = Flask(__name__)
CORS(app)

load_dotenv()

# Service URLs
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:5001")  
EVENT_SERVICE_URL = "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI"
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5100")

#RabbitMQ configuration
EXCHANGE_NAME = "ticketing.exchange"
ROUTING_KEY = "ticket.transfer.pending"

def send_transfer_notification(sender_email, recipient_email, ticket_id, event_name):
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
            "email": recipient_email,
            "eventType": "ticket.transfer.pending",
            "sender_email": sender_email,
            "ticket_id": ticket_id,
            "ticketNumber": ticket_id,
            "eventName": event_name
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

@app.route("/validateTransfer/<ticket_id>", methods=["POST"])
def validate_transfer(ticket_id):
    """
    Validates if a ticket can be transferred based on:
    1. Ticket transferability (is_transferable boolean from ticket service)
    2. Event date validation (not within 3 days of event)
    3. Recipient email validation (must exist in user service)
    """
    try:
        data = request.json
        recipient_email = data.get("recipientEmail")
        sender_email = data.get("senderEmail")

        if not recipient_email or not sender_email:
            return jsonify({
                "error": "Missing required fields",
                "message": "Both recipient and sender email are required"
            }), 400

        # Step 1: Check ticket transferability
        ticket_validation = validate_ticket(ticket_id)
        if not ticket_validation["is_valid"]:
            return jsonify({
                "can_transfer": False,
                "message": ticket_validation["messages"][0]
            }), 400

        # Step 2: Check event date (only if ticket is transferable)
        event_validation = validate_event(
            ticket_validation["event_id"], 
            ticket_validation["event_date_id"]
        )
        if not event_validation["is_valid"]:
            return jsonify({
                "can_transfer": False,
                "message": event_validation["messages"][0]
            }), 400

        # Step 3: Validate recipient email
        recipient_validation = validate_recipient(recipient_email)
        if not recipient_validation["is_valid"]:
            return jsonify({
                "can_transfer": False,
                "message": recipient_validation["messages"][0]
            }), 400

        # Extract event name from validation message
        event_name = event_validation["messages"][0].split("'")[1] 

        # Step 4: Send notification
        notification_sent = send_transfer_notification(
            sender_email=sender_email,
            recipient_email=recipient_email,
            ticket_id=ticket_id,
            event_name=event_name
        )

        # All validations passed
        return jsonify({
            "can_transfer": True,
            "message": "Ticket is eligible for transfer",
            "ticket_id": ticket_id,
            "recipient_email": recipient_email,
            "notification_sent": notification_sent
        })

    except Exception as e:
        return jsonify({
            "error": "Validation service error",
            "message": str(e)
        }), 500

def validate_ticket(ticket_id):
    try:
        # Get ticket details directly
        response = requests.get(f"{TICKET_SERVICE_URL}/tickets/{ticket_id}")
        if response.status_code != 200:
            return {
                "is_valid": False,
                "messages": ["Ticket not found"],
                "event_date_id": None,
                "event_id": None
            }

        ticket_data = response.json()
        is_transferable = ticket_data.get("is_transferable", False)
        
        return {
            "is_valid": is_transferable,
            "messages": ["Ticket is transferable"] if is_transferable else ["Ticket is not transferable"],
            "event_date_id": ticket_data.get("event_date_id"),
            "event_id": ticket_data.get("event_id")
        }

    except Exception as e:
        return {
            "is_valid": False,
            "messages": [f"Error checking ticket transferability: {str(e)}"],
            "event_date_id": None,
            "event_id": None
        }

def validate_event(event_id, event_date_id):
    try:
        # Get all events
        response = requests.get(f"{EVENT_SERVICE_URL}/events")
        if response.status_code != 200:
            return {
                "is_valid": False,
                "messages": ["Event not found or invalid"]
            }

        event_data = response.json()
        if not event_data.get("Result", {}).get("Success", False):
            return {
                "is_valid": False,
                "messages": ["Failed to retrieve event data"]
            }

        # Find the specific event date from the list
        event = None
        for e in event_data.get("Events", []):
            if e["EventId"] == event_id and e["EventDateId"] == event_date_id:
                event = e
                break

        if not event:
            return {
                "is_valid": False,
                "messages": [f"No data found for event ID {event_id} and event date ID {event_date_id}"]
            }

        event_date = datetime.strptime(event["Date"], "%Y-%m-%dT%H:%M:%SZ")
        event_name = event["Name"]
        current_date = datetime.now()

        # Calculate days until event
        days_until_event = (event_date - current_date).days

        # Check if event has passed or is within 3 days
        if days_until_event < 0:
            return {
                "is_valid": False,
                "messages": [f"Event '{event_name}' has already passed (date was: {event_date.strftime('%Y-%m-%d')})"]
            }
        elif days_until_event < 3:
            return {
                "is_valid": False,
                "messages": [f"Event '{event_name}' is within 3 days (date: {event_date.strftime('%Y-%m-%d')})"]
            }
        else:
            return {
                "is_valid": True,
                "messages": [f"Event '{event_name}' is valid (date: {event_date.strftime('%Y-%m-%d')}, {days_until_event} days away)"]
            }

    except Exception as e:
        return {
            "is_valid": False,
            "messages": [f"Error validating event: {str(e)}"]
        }

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004, debug=True)
