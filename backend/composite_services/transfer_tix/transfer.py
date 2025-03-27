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
ORDER_SERVICE_URL = "http://order-service:8003"
TICKET_SERVICE_URL = "http://ticket-service:5001"
VALIDATE_SERVICE_URL = "http://validate-service:8004"
USER_SERVICE_URL = "http://user-service:5003"

# RabbitMQ configuration
EXCHANGE_NAME = "ticketing.exchange"
ROUTING_KEY = "ticket.transfer.success"

@app.route("/transfer/<ticket_id>", methods=["POST"])
def transfer_ticket(ticket_id):
    """
    Complete the ticket transfer after recipient acceptance.
    Required request body:
    {
        "sender_id": "123",
        "sender_email": "sender@example.com",
        "recipient_email": "recipient@example.com",
        "accepted": true
    }
    """
    try:
        data = request.json
        
        # Check if transfer was accepted by recipient
        if not data.get("accepted", False):
            # If rejected, update ticket status back to "sold" and remove pending_transfer_to
            ticket_response = requests.put(
                f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                json={
                    "status": "sold",
                    "pending_transfer_to": None  # Remove pending transfer
                }
            )
            
            return jsonify({
                "success": False,
                "message": "Transfer rejected by recipient"
            }), 200

        # Get recipient's user ID from email
        recipient_email = data.get('recipient_email')
        recipient_response = requests.get(
            f"{USER_SERVICE_URL}/user/email/{recipient_email}"
        )
        
        if recipient_response.status_code != 200:
            return jsonify({
                "error": "Invalid recipient",
                "message": f"Could not find user with email {recipient_email}"
            }), 400
            
        recipient_data = recipient_response.json()
        recipient_id = recipient_data.get("user_id")

        if not recipient_id:
            return jsonify({
                "error": "User data error",
                "message": "Could not get user ID from response"
            }), 400

        # Revalidate the transfer to ensure conditions are still valid
        validation_response = requests.post(
            f"{VALIDATE_SERVICE_URL}/validateTransfer/{ticket_id}",
            json={
                "senderEmail": data.get("sender_email"),
                "recipientEmail": recipient_email
            }
        ).json()
        
        if not validation_response.get("can_transfer", False):
            # Reset ticket status back to "sold" if validation fails
            ticket_response = requests.put(
                f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                json={
                    "status": "SOLD"
                }
            )
            
            return jsonify({
                "error": "Validation failed",
                "message": validation_response.get("message", "Transfer conditions are no longer valid")
            }), 400

        # Get ticket details for event information
        ticket_details_response = requests.get(f"{TICKET_SERVICE_URL}/tickets/{ticket_id}")
        if ticket_details_response.status_code != 200:
            return jsonify({
                "error": "Failed to get ticket details",
                "message": "Could not retrieve ticket information"
            }), 400
            
        ticket_details = ticket_details_response.json()
        
        # Validate required fields exist
        required_fields = ["event_id", "event_date_id", "cat_id"]
        missing_fields = [field for field in required_fields if not ticket_details.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": "Missing ticket details",
                "message": f"Ticket is missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Create transfer order with validated data
        order_request_data = {
            "ticketId": str(ticket_id),
            "fromUserId": str(data.get("sender_id")),
            "toUserId": str(recipient_id),
            "eventId": int(ticket_details["event_id"]),
            "eventDateId": int(ticket_details["event_date_id"]),
            "catId": int(ticket_details["cat_id"])
        }
        
        # Debug logging
        print("\n=== Transfer Debug Information ===")
        print("Ticket Details:", json.dumps(ticket_details, indent=2, default=str))
        print("\nOrder Request Data:", json.dumps(order_request_data, indent=2))
        print("\nMaking request to:", f"{ORDER_SERVICE_URL}/orders/transfer")
        print("=================================\n")
        
        try:
            # Add more detailed request debugging
            print("Request Headers:", {'Content-Type': 'application/json'})
            print("Request Body:", json.dumps(order_request_data, indent=2))
            
            order_response = requests.post(
                f"{ORDER_SERVICE_URL}/orders/transfer",
                json=order_request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Detailed response debugging
            print("Order Response Status:", order_response.status_code)
            print("Order Response Headers:", order_response.headers)
            print("Order Response Content:", order_response.text)
            
        except requests.exceptions.RequestException as e:
            print("Request Exception:", str(e))
            return jsonify({
                "error": "Connection error to order service",
                "message": str(e)
            }), 500

        if order_response.status_code != 201:
            return jsonify({
                "error": "Failed to create transfer order",
                "message": f"Order service error: {order_response.text}"
            }), 500

        order_data = order_response.json()

        # Update ticket ownership and status in Ticket Service
        ticket_response = requests.put(
            f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
            json={
                "owner_id": recipient_id,
                "status": "TRANSFERRED",
                "pending_transfer_to": None  # Remove pending transfer after successful transfer
            }
        ).json()

        # After successful ticket update, get event name from validation response
        # Get event name from ticket details or validation response
        event_name = ticket_details.get("event_name", "Event")  # Use ticket details for event name

        # Send success notifications
        notification_sent = send_transfer_success_notification(
            sender_email=data.get("sender_email"),
            recipient_email=data.get("recipient_email"),
            ticket_id=ticket_id,
            event_name=event_name
        )

        return jsonify({
            "success": True,
            "message": "Ticket transferred successfully",
            "transfer_details": {
                "ticket_id": ticket_id,
                "from_user_id": data.get("sender_id"),
                "to_user_id": recipient_id,
                "transfer_date": datetime.now().isoformat(),
                "order_id": order_data.get("orderId"),
                "notification_sent": notification_sent
            }
        }), 200

    except Exception as e:
        # In case of error, attempt to reset ticket status
        try:
            requests.put(
                f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                json={
                    "status": "SOLD",
                    "pending_transfer_to": None
                }
            )
        except:
            pass  # Ignore errors in cleanup
            
        return jsonify({
            "error": "Transfer service error",
            "message": str(e)
        }), 500

# Add this function to send notifications
def send_transfer_success_notification(sender_email, recipient_email, ticket_id, event_name):
    try:
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host='host.docker.internal',  # Make sure this is correct for your setup
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

        # Send notification to recipient
        recipient_message = {
            "email": recipient_email,
            "eventType": "ticket.transfer.success",
            "sender_email": sender_email,
            "ticket_id": ticket_id,
            "ticketNumber": ticket_id,
            "eventName": event_name,
            "role": "recipient"
        }

        # Send notification to sender
        sender_message = {
            "email": sender_email,
            "eventType": "ticket.transfer.success",
            "recipient_email": recipient_email,
            "ticket_id": ticket_id,
            "ticketNumber": ticket_id,
            "eventName": event_name,
            "role": "sender"
        }

        # Publish both messages with the correct routing key
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(recipient_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(sender_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )

        connection.close()
        return True
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8011, debug=True)
