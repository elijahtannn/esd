from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import pika
import json
import logging
import random
import string

app = Flask(__name__)
CORS(app)

load_dotenv()
# Service URLs
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002")
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:5001")
EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5003")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8003")

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "host.docker.internal")
EXCHANGE_NAME = "ticketing.exchange"
ROUTING_KEY = "ticket.purchase"

# def send_purchase_notification(user_email, event_name, order_id, event_date, ticket_ids):
#     try:
#         credentials = pika.PlainCredentials('guest', 'guest')
#         parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=5672, credentials=credentials)
#         connection = pika.BlockingConnection(parameters)
#         channel = connection.channel()

#         channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

#         message = {
#             "email": user_email,
#             "eventType": "ticket.purchase",
#             "event_name": event_name,
#             "order_id": order_id,
#             "eventDate": event_date,
#             "ticketNumber": ",".join(map(str, ticket_ids))
#         }

#         channel.basic_publish(
#             exchange=EXCHANGE_NAME,
#             routing_key=ROUTING_KEY,
#             body=json.dumps(message),
#             properties=pika.BasicProperties(delivery_mode=2)
#         )

#         connection.close()
#         return True
#     except Exception as e:
#         print(f"Error sending RabbitMQ message: {str(e)}")
#         return False

logging.basicConfig(level=logging.INFO)

@app.route("/process_ticket_order", methods=["POST"])
def process_ticket_order():
    try:
        data = request.json
        user_id = data.get("user_id")
        event_id = data.get("EventId")
        event_date_id = data.get("EventDateId")
        ticket_arr = data.get("ticketArr")
        payment_token = data.get("payment_token")

        if not all([user_id, event_id, event_date_id, ticket_arr, payment_token]):
            return jsonify({"error": "Missing required fields"}), 400

        # Fetch user email
        user_resp = requests.get(f"{USER_SERVICE_URL}/user/{user_id}")
        if user_resp.status_code != 200:
            return jsonify({"error": "User not found"}), 404

        user_email = user_resp.json().get("email")
        all_reserved_ticket_ids = []
        total_amount = 0

        for item in ticket_arr:
            cat_id = item.get("catId")
            quantity = item.get("quantity")
            price = item.get("price")

            query_params = {
                "owner_id": user_id,
                "cat_id": cat_id,
                "event_id": event_id,
                "event_date_id": event_date_id,
                "status": "reserved"
            }
            response = requests.get(f"{TICKET_SERVICE_URL}/tickets", params=query_params)
            if response.status_code != 200:
                return jsonify({"error": "Failed to fetch reserved tickets"}), 400

            reserved_tickets = response.json()
            matching_tickets = [t for t in reserved_tickets if t["status"] == "reserved"]

            selected_ids = [t["_id"] for t in matching_tickets[:quantity]]
            all_reserved_ticket_ids.extend(selected_ids)
            total_amount += price * quantity

        # Process payment
        payment_data = {
            "user_id": user_id,
            "amount": total_amount,
            "payment_token": payment_token
        }
        payment_resp = requests.post(f"{PAYMENT_SERVICE_URL}/payments/process", json=payment_data)
        if payment_resp.status_code != 201:
            return jsonify({"error": "Payment failed", "details": payment_resp.text}), 400

        payment_id = payment_resp.json().get("payment_id") or payment_resp.json().get("transaction_id")

        # Confirm tickets
        confirm_data = {
            "ticket_ids": all_reserved_ticket_ids
        }
        confirm_resp = requests.put(f"{TICKET_SERVICE_URL}/tickets/confirm", json=confirm_data)
        if confirm_resp.status_code != 200:
            return jsonify({"error": "Ticket confirmation failed", "details": confirm_resp.text}), 400

        # Fetch extra order details from request
        event_name = data.get("eventName", "")
        event_date = data.get("eventDate", "")
        venue = data.get("venue", "")
        created_orders = []
        ticket_idx = 0
        for item in ticket_arr:
            cat_id = item.get("catId")
            quantity = item.get("quantity")
            price = item.get("price")
            ticket_ids = all_reserved_ticket_ids[ticket_idx:ticket_idx + quantity]
            ticket_idx += quantity

            order_data = {
            "userId": user_id,
            "ticketIds": ticket_ids,
            "eventId": event_id,
            "eventDateId": event_date_id,
            "eventName": event_name,
            "venue": venue,
            "catId": cat_id,
            "orderType": "PURCHASE",
            "totalAmount": quantity * price,
            "paymentId": payment_id
            }

            order_resp = requests.post(f"{ORDER_SERVICE_URL}/orders", json=order_data)
            if order_resp.status_code != 201:
                return jsonify({"error": "Order creation failed", "details": order_resp.text}), 400
            created_orders.append(order_resp.json())  # Collect successful order

        # Send notification via RabbitMQ
        try:
            credentials = pika.PlainCredentials('guest', 'guest')
            parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=5672, credentials=credentials)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

            message = {
                "email": user_email,
                "eventType": "ticket.purchase",
                "eventName": event_name,
                "order_id": created_orders[0]["orderId"] if created_orders else "N/A",
                "eventDate": event_date,
                "ticketNumber": ",".join([tid for order in created_orders for tid in order["ticketIds"]])
            }
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
        except Exception as e:
            print(f"Error sending RabbitMQ message: {str(e)}")

        return jsonify({
            "status": "success",
            "orders": created_orders
        }), 200

    except Exception as e:
        logging.exception("Unexpected error during ticket order processing")
        return jsonify({"error": "Service error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)