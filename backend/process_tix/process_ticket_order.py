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
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://host.docker.internal:5001")
EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://user-service:8000")

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "host.docker.internal")
EXCHANGE_NAME = "ticketing.exchange"
ROUTING_KEY = "ticket.purchase.success"

def send_purchase_notification(user_email, event_name, order_id):
    try:
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=5672, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

        message = {
            "email": user_email,
            "eventType": "ticket.purchase.success",
            "event_name": event_name,
            "order_id": order_id
        }

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        connection.close()
        return True
    except Exception as e:
        print(f"Error sending RabbitMQ message: {str(e)}")
        return False

def check_event_inventory(event_id, event_date_id, ticket_quantity):
    try:
        response = requests.get(f"{EVENT_SERVICE_URL}/events", timeout=10)
        if response.status_code != 200:
            return False, f"Failed to retrieve event data, status code: {response.status_code}", None, None

        try:
            event_data = json.loads(response.content.decode("utf-8-sig"))
        except json.JSONDecodeError as e:
            print("JSON decode failed:", response.content)
            return False, f"JSON parsing error: {str(e)}", None, None

        for event in event_data.get("Events", []):
            if event["EventId"] == event_id and event["EventDateId"] == event_date_id:
                available_tickets = event["AvailableTickets"]
                if available_tickets >= ticket_quantity:
                    return True, event["Name"], event["Date"], event["Venue"]
                else:
                    return False, f"Insufficient tickets: Requested {ticket_quantity}, but only {available_tickets} available.", None, None

        return False, "Event not found", None, None

    except Exception as e:
        return False, f"Error checking inventory: {str(e)}", None, None

def fetch_category_price(event_date_id, cat_id):
    try:
        url = f"{EVENT_SERVICE_URL}/events/dates/{event_date_id}/categories"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch category data, status code: {response.status_code}")
        data = response.json()
        for cat in data.get("Cats", []):
            if cat.get("Id") == cat_id:
                return cat.get("Price")
        raise Exception("Category not found")
    except Exception as e:
        raise Exception(f"Failed to fetch price: {str(e)}")

logging.basicConfig(level=logging.INFO)

@app.route("/process_ticket_order", methods=["POST"])
def process_ticket_order():
    try:
        data = request.json
        user_id = data.get("user_id")
        event_id = data.get("EventId")
        event_date_id = data.get("EventDateId")
        ticket_quantity = data.get("ticket_quantity")
        seat_info = data.get("seat_info", "General Admission")
        cat_id = data.get("cat_id", 1)

        if not all([user_id, event_id, event_date_id, ticket_quantity, cat_id]):
            return jsonify({"error": "Missing required fields"}), 400

        user_resp = requests.get(f"{USER_SERVICE_URL}/user/{user_id}")
        if user_resp.status_code != 200 or not user_resp.content:
            return jsonify({"error": "User not found", "details": user_resp.text}), 404
        user_email = user_resp.json().get("email")

        inventory_available, event_name, event_date, venue = check_event_inventory(event_id, event_date_id, ticket_quantity)
        if not inventory_available:
            return jsonify({"error": event_name}), 400

        ticket_price = fetch_category_price(event_date_id, cat_id)

        reserve_data = {
            "event_date_id": event_date_id,
            "cat_id": cat_id,
            "owner_id": user_id,
            "seat_info": seat_info,
            "num_tickets": ticket_quantity
        }
        reserve_resp = requests.post(f"{TICKET_SERVICE_URL}/tickets/reserve", json=reserve_data)

        try:
            reserve_result = reserve_resp.json()
            reserved_ticket_ids = reserve_result.get("ticket_ids", [])
            if not reserved_ticket_ids:
                return jsonify({"error": "No ticket IDs returned", "details": reserve_result}), 400
        except Exception as e:
            return jsonify({"error": "Failed to parse ticket reservation response", "details": str(e)}), 400

        payment_data = {
            "user_id": user_id,
            "amount": ticket_quantity * ticket_price,
            "payment_token": data.get("payment_token")
        }
        payment_resp = requests.post(f"{PAYMENT_SERVICE_URL}/payments/process", json=payment_data)
        if payment_resp.status_code != 201 or not payment_resp.content:
            requests.post(f"{TICKET_SERVICE_URL}/tickets/release", json=reserve_data)
            return jsonify({"error": "Payment failed", "details": payment_resp.text}), 400

        payment_id = payment_resp.json().get("payment_id") or payment_resp.json().get("transaction_id")

        confirm_data = {
            "user_id": user_id,
            "order_id": payment_id,
            "ticket_ids": reserved_ticket_ids
        }
        confirm_resp = requests.put(f"{TICKET_SERVICE_URL}/tickets/confirm", json=confirm_data)
        if confirm_resp.status_code != 200:
            return jsonify({"error": "Ticket confirmation failed", "details": confirm_resp.text}), 400

        order_data = {
            "userId": user_id,
            "ticketIds": reserved_ticket_ids,
            "eventId": event_id,
            "eventName": event_name,
            "eventDate": event_date,
            "venue": venue,
            "orderType": "PURCHASE",
            "totalAmount": ticket_quantity * ticket_price,
            "paymentId": payment_id
        }
        order_resp = requests.post(f"{ORDER_SERVICE_URL}/orders", json=order_data)
        if order_resp.status_code != 201 or not order_resp.content:
            return jsonify({"error": "Order creation failed", "details": order_resp.text}), 400

        order_id = order_resp.json().get("orderId")

        notification_sent = send_purchase_notification(user_email=user_email, event_name=event_name, order_id=order_id)

        return jsonify({
            "status": "success",
            "order_id": order_id,
            "notification_sent": notification_sent
        }), 200

    except Exception as e:
        logging.exception("Unexpected error during ticket order processing")
        return jsonify({"error": "Service error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
