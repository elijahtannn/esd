from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import pika
import json
import logging

app = Flask(__name__)
CORS(app)

load_dotenv()
# Service URLs
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://user-service:8002")
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://host.docker.internal:5001")  # Use host.docker.internal to access host machine
EVENT_SERVICE_URL = "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI"
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://user-service:8000")


# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "host.docker.internal")
EXCHANGE_NAME = "ticketing.exchange"
ROUTING_KEY = "ticket.purchase.success"


# RabbitMQ Connection
def send_purchase_notification(user_email, event_name, order_id):
    """
    Sends a ticket purchase notification via RabbitMQ.
    """
    try:
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
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
            "email": user_email,
            "eventType": "ticket.purchase.success",
            "event_name": event_name,
            "order_id": order_id
        }

        # Publish message
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )

        connection.close()
        return True
    except Exception as e:
        print(f"Error sending RabbitMQ message: {str(e)}")
        return False

def check_event_inventory(event_id, event_date_id, ticket_quantity):
    """
    Fetches all events and checks if the requested event date has enough available tickets.
    """
    try:
        response = requests.get(EVENT_SERVICE_URL, timeout=10)

        if response.status_code != 200:
            return False, f"Failed to retrieve event data, status code: {response.status_code}"

        event_data = json.loads(response.content.decode("utf-8-sig"))

        # Find the specific event occurrence by EventId and EventDateId
        for event in event_data.get("Events", []):
            if event["EventId"] == event_id and event["EventDateId"] == event_date_id:
                available_tickets = event["AvailableTickets"]

                # 🔹 Add a log to debug ticket availability
                print(f"DEBUG: Event {event_id}, Date {event_date_id}, Available Tickets: {available_tickets}")

                if available_tickets >= ticket_quantity:
                    return True, event["Name"]  # Return event name if inventory is sufficient
                else:
                    return False, f"Insufficient tickets: Requested {ticket_quantity}, but only {available_tickets} available."

        return False, "Event not found"
    
    except json.JSONDecodeError as e:
        return False, f"Error parsing JSON: {str(e)}"
    except requests.exceptions.Timeout:
        return False, "Event API timeout (took too long to respond)"
    except Exception as e:
        return False, f"Error checking inventory: {str(e)}"


# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route("/process_ticket_order", methods=["POST"])
def process_ticket_order():
    """Process ticket order and send notification via RabbitMQ."""
    try:
        data = request.json
        user_id = data.get("user_id")
        event_id = data.get("EventId")
        event_date_id = data.get("EventDateId")  # Added event_date_id
        ticket_quantity = data.get("ticket_quantity")

        if not all([user_id, event_id, event_date_id, ticket_quantity]):
            return jsonify({"error": "Missing required fields"}), 400

        logging.info(f"Processing ticket order for User: {user_id}, Event: {event_id}, EventDate: {event_date_id}, Quantity: {ticket_quantity}")

        # Step 1: Validate User
        user_resp = requests.get(f"{USER_SERVICE_URL}/user/{user_id}")
        if user_resp.status_code != 200:
            logging.error(f"User {user_id} not found. Response: {user_resp.text}")
            return jsonify({"error": "User not found"}), 404

        user_data = user_resp.json()
        user_email = user_data.get("email")

        # Step 2: Check Event Ticket Availability
        inventory_available, event_name = check_event_inventory(event_id, event_date_id, ticket_quantity)
        if not inventory_available:
            logging.warning(f"Insufficient tickets for Event: {event_id}, Date: {event_date_id}")
            return jsonify({"error": event_name}), 400

        # Step 3: Reserve Ticket
        reserve_data = {"user_id": user_id, "event_id": event_id, "event_date_id": event_date_id, "ticket_quantity": ticket_quantity}
        reserve_resp = requests.post(f"{TICKET_SERVICE_URL}/reserve", json=reserve_data)
        if reserve_resp.status_code != 200:
            logging.error(f"Ticket reservation failed. Response: {reserve_resp.text}")
            return jsonify({"error": "Ticket reservation failed"}), 400

        # Step 4: Process Payment
        payment_data = {"user_id": user_id, "amount": ticket_quantity * 50}  # Example price
        payment_resp = requests.post(f"{PAYMENT_SERVICE_URL}/payments/process", json=payment_data)
        if payment_resp.status_code != 200:
            logging.error(f"Payment failed. Rolling back reservation. Response: {payment_resp.text}")
            requests.post(f"{TICKET_SERVICE_URL}/release", json=reserve_data)  # Rollback reservation
            return jsonify({"error": "Payment failed"}), 400

        payment_id = payment_resp.json().get("payment_id")

        # Step 5: Confirm Ticket
        confirm_resp = requests.put(f"{TICKET_SERVICE_URL}/tickets/confirm", json={"order_id": payment_id, "user_id": user_id})
        if confirm_resp.status_code != 200:
            logging.error(f"Ticket confirmation failed. Response: {confirm_resp.text}")
            return jsonify({"error": "Ticket confirmation failed"}), 400

        # Step 6: Create Order
        order_data = {"user_id": user_id, "event_id": event_id, "event_date_id": event_date_id, "payment_id": payment_id, "ticket_quantity": ticket_quantity}
        order_resp = requests.post(f"{ORDER_SERVICE_URL}/orders", json=order_data)
        if order_resp.status_code != 200:
            logging.error(f"Order creation failed. Response: {order_resp.text}")
            return jsonify({"error": "Order creation failed"}), 400

        order_id = order_resp.json().get("order_id")

        # Step 7: Update Ticket Inventory
        update_data = {"event_id": event_id, "event_date_id": event_date_id, "ticket_quantity": -ticket_quantity}
        update_resp = requests.put(f"{EVENT_SERVICE_URL}/{event_date_id}/inventory", json=update_data)
        if update_resp.status_code != 200:
            logging.error(f"Failed to update event inventory. Response: {update_resp.text}")
            return jsonify({"error": "Failed to update event inventory"}), 400

        # Step 8: Notify User via RabbitMQ
        notification_sent = send_purchase_notification(user_email=user_email, event_name=event_name, order_id=order_id)

        response = {
            "status": "success",
            "order_id": order_id,
            "notification_sent": notification_sent
        }
        logging.info(f"Order {order_id} processed successfully!")
        return jsonify(response), 200

    except Exception as e:
        logging.exception("Unexpected error during ticket order processing")
        return jsonify({"error": "Service error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)