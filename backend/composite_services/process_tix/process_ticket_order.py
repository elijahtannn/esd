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
        # Instead of a flat list, we build a dictionary to group ticket IDs by catId
        tickets_by_cat = {}
        total_amount = 0

        # Loop through each ticket category to gather reserved ticket IDs
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
            if len(matching_tickets) < quantity:
                return jsonify({"error": f"Not enough reserved tickets for category {cat_id}"}), 400

            selected_ids = [t["_id"] for t in matching_tickets[:quantity]]
            # Group the ticket IDs by category
            if cat_id in tickets_by_cat:
                tickets_by_cat[cat_id].extend(selected_ids)
            else:
                tickets_by_cat[cat_id] = selected_ids

            total_amount += price * quantity

        # Flatten all ticket IDs if needed for other purposes:
        all_ticket_ids = []
        for ids in tickets_by_cat.values():
            all_ticket_ids.extend(ids)

        # Confirm all reserved tickets at once (mark them as sold)
        confirm_data = {"ticket_ids": all_ticket_ids}
        confirm_resp = requests.put(f"{TICKET_SERVICE_URL}/tickets/confirm", json=confirm_data)
        if confirm_resp.status_code != 200:
            return jsonify({"error": "Ticket confirmation failed", "details": confirm_resp.text}), 400

        # Process payment for the total amount
        payment_data = {
            "user_id": user_id,
            "amount": total_amount,
            "payment_token": payment_token
        }
        payment_resp = requests.post(f"{PAYMENT_SERVICE_URL}/payments/process", json=payment_data)
        if payment_resp.status_code != 201:
            return jsonify({"error": "Payment failed", "details": payment_resp.text}), 400

        payment_id = payment_resp.json().get("payment_id") or payment_resp.json().get("transaction_id")

        # Build the nested structure for tickets
        nested_ticket_ids = [{"catId": cat, "ticketIds": ids} for cat, ids in tickets_by_cat.items()]

        # Create a single order with the nested ticket IDs and the total amount
        order_data = {
            "userId": user_id,
            "ticketIds": all_ticket_ids,  # Optionally include the flat list as well
            "tickets": nested_ticket_ids, # Nested array of ticket IDs by category
            "eventId": event_id,
            "eventDateId": event_date_id,
            "orderType": "PURCHASE",
            "totalAmount": total_amount,
            "paymentId": payment_id,
            "eventName": data.get("eventName", ""),
            "venue": data.get("venue", "")
        }
        order_resp = requests.post(f"{ORDER_SERVICE_URL}/orders", json=order_data)
        if order_resp.status_code != 201:
            return jsonify({"error": "Order creation failed", "details": order_resp.text}), 400

        created_order = order_resp.json()

        # Send notification via RabbitMQ (unchanged)
        try:
            credentials = pika.PlainCredentials('guest', 'guest')
            parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=5672, credentials=credentials)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

            message = {
                "email": user_email,
                "eventType": "ticket.purchase",
                "event_name": data.get("eventName", ""),
                "order_id": created_order.get("orderId", "N/A"),
                "eventDate": data.get("eventDate", ""),
                "ticketNumber": ",".join(all_ticket_ids)
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
            "status": "SUCCESS",
            "order": created_order
        }), 200

    except Exception as e:
        logging.exception("Unexpected error during ticket order processing")
        return jsonify({"error": "Service error", "message": str(e)}), 500