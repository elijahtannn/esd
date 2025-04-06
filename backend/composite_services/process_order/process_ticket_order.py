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

logging.basicConfig(level=logging.INFO)

@app.route("/process_ticket_order", methods=["POST"])
def process_ticket_order():
    try:
        data = request.json
        user_id = data.get("user_id")
        event_id = data.get("event_id")
        event_date_id = data.get("event_date_id")
        ticket_arr = data.get("ticket_arr")
        payment_token = data.get("payment_token")
        user_email = data.get("user_email")

        if not all([user_id, event_id, event_date_id, ticket_arr, payment_token]):
            return jsonify({"error": "Missing required fields"}), 400

        
        total_amount = sum(item.get("price", 0) * item.get("quantity", 0) for item in ticket_arr)

        payment_data = {
            "user_id": user_id,
            "amount": total_amount,
            "payment_token": payment_token
        }
        
        payment_resp = requests.post(f"{PAYMENT_SERVICE_URL}/payments/process", json=payment_data)
        if payment_resp.status_code != 201:
            return jsonify({"error": "Payment failed", "details": payment_resp.text}), 400

        payment_id = payment_resp.json().get("payment_id") or payment_resp.json().get("transaction_id")

        
        tickets_by_cat = {}

        # Loop through each ticket category to gather reserved ticket IDs
        for item in ticket_arr:
            cat_id = item.get("catId")
            quantity = item.get("quantity")
            
            query_params = {
                "owner_id": user_id,
                "cat_id": cat_id,
                "event_id": event_id,
                "event_date_id": event_date_id,
                "status": "RESERVED"
            }
            response = requests.get(f"{TICKET_SERVICE_URL}/tickets/category/{cat_id}", params=query_params)
            if response.status_code != 200:
                return jsonify({"error": "Failed to fetch reserved tickets"}), 404

            reserved_tickets = response.json()
            matching_tickets = [t for t in reserved_tickets if t["status"] == "RESERVED"]
            if len(matching_tickets) < quantity:
                return jsonify({"error": f"Not enough reserved tickets for category {cat_id}"}), 404

            selected_ids = [t["_id"] for t in matching_tickets[:quantity]]
            
            if cat_id in tickets_by_cat:
                tickets_by_cat[cat_id].extend(selected_ids)
            else:
                tickets_by_cat[cat_id] = selected_ids
            print("DEBUG: selected_ids for cat", cat_id, "=", selected_ids)

        # Flatten all ticket IDs if needed for other purposes:
        all_ticket_ids = []
        for ids in tickets_by_cat.values():
            all_ticket_ids.extend(ids)

        # Confirm all reserved tickets at once (mark them as sold)
        confirm_data = {"ticket_ids": all_ticket_ids}
        confirm_resp = requests.put(f"{TICKET_SERVICE_URL}/tickets/confirm", json=confirm_data)
        
        if confirm_resp.status_code != 200:
            return jsonify({"error": "Ticket confirmation failed", "details": confirm_resp.text}), 404

        # Build the nested structure for tickets
        nested_ticket_ids = [{"catId": cat, "ticketIds": ids} for cat, ids in tickets_by_cat.items()]

        # Create a single order with the nested ticket IDs and the total amount
        order_data = {
            "userId": user_id,
            "tickets": nested_ticket_ids,
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
            # Log the error response for debugging
            logging.error(f"Order creation failed. Response: {order_resp.text}")
            return jsonify({"error": "Order creation failed", "details": order_resp.text}), 400

        created_order = order_resp.json()

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
                "eventName": data.get("eventName", ""),  
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)