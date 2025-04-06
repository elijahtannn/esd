from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import pika
import json
import time
from requests.exceptions import RequestException

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

def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Retry a function with exponential backoff"""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func()
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(delay)
            delay *= 2

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
        print(f"\n=== Transfer Completion Debug ===")
        print(f"Processing transfer for ticket {ticket_id}")
        print(f"Current timestamp: {datetime.utcnow()}")
        
        data = request.json
        print(f"Request data: {data}")
        
        # Check if transfer was accepted by recipient
        if not data.get("accepted", False):
            print("Transfer was rejected by recipient")
            # If rejected, update ticket status back to "sold" and remove pending_transfer_to
            def reject_transfer():
                return requests.put(
                    f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                    json={
                        "status": "SOLD",
                        "pending_transfer_to": None  
                    }
                )
            
            retry_with_backoff(reject_transfer)
            
            return jsonify({
                "success": False,
                "message": "Transfer rejected by recipient"
            }), 200

        # Get recipient's user ID from email
        recipient_email = data.get('recipient_email')
        print(f"Getting recipient ID for email: {recipient_email}")
        
        def get_recipient():
            return requests.get(f"{USER_SERVICE_URL}/user/email/{recipient_email}")
            
        recipient_response = retry_with_backoff(get_recipient)
        
        if recipient_response.status_code != 200:
            print(f"Failed to get recipient ID. Status: {recipient_response.status_code}")
            return jsonify({
                "error": "Invalid recipient",
                "message": f"Could not find user with email {recipient_email}"
            }), 400
            
        recipient_data = recipient_response.json()
        recipient_id = recipient_data.get("user_id")
        print(f"Recipient ID: {recipient_id}")

        if not recipient_id:
            print("No recipient ID found in response")
            return jsonify({
                "error": "User data error",
                "message": "Could not get user ID from response"
            }), 400

        # Revalidate the transfer to ensure conditions are still valid
        print("\nRevalidating transfer...")
        def revalidate():
            return requests.post(
                f"{VALIDATE_SERVICE_URL}/validateTransfer/{ticket_id}",
                json={
                    "senderEmail": data.get("sender_email"),
                    "recipientEmail": recipient_email,
                    "is_revalidation": True
                }
            )
            
        validation_response = retry_with_backoff(revalidate).json()
        
        if not validation_response.get("can_transfer", False):
            print(f"Revalidation failed: {validation_response.get('message')}")
            # Reset ticket status back to "sold" if validation fails
            def reset_ticket():
                return requests.put(
                    f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                    json={
                        "status": "SOLD"
                    }
                )
                
            retry_with_backoff(reset_ticket)
            
            return jsonify({
                "error": "Validation failed",
                "message": validation_response.get("message", "Transfer conditions are no longer valid")
            }), 400
        print("Revalidation successful")

        # Get ticket details for event information
        print("\nGetting ticket details...")
        def get_ticket_details():
            return requests.get(f"{TICKET_SERVICE_URL}/tickets/{ticket_id}")
            
        ticket_details_response = retry_with_backoff(get_ticket_details)
        
        if ticket_details_response.status_code != 200:
            print(f"Failed to get ticket details. Status: {ticket_details_response.status_code}")
            return jsonify({
                "error": "Failed to get ticket details",
                "message": "Could not retrieve ticket information"
            }), 400
            
        ticket_details = ticket_details_response.json()
        print(f"Ticket details: {ticket_details}")
        
        # Validate required fields exist
        required_fields = ["event_id", "event_date_id", "cat_id"]
        missing_fields = [field for field in required_fields if not ticket_details.get(field)]
        
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
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
        
        
        def create_order():
            return requests.post(
                f"{ORDER_SERVICE_URL}/orders/transfer",
                json=order_request_data,
                headers={'Content-Type': 'application/json'}
            )
            
        order_response = retry_with_backoff(create_order)
        
        if order_response.status_code != 201:
            print(f"Failed to create transfer order. Status: {order_response.status_code}")
            return jsonify({
                "error": "Failed to create transfer order",
                "message": f"Order service error: {order_response.text}"
            }), 500

        order_data = order_response.json()
        print(f"Transfer order created: {order_data}")

        # Update ticket ownership and status in Ticket Service
        print("\nUpdating ticket ownership...")
        ticket_update_data = {
            "owner_id": recipient_id,
            "status": "SOLD",
            "pending_transfer_to": None,
            "is_transferable": False
        }
        print(f"Ticket update data: {ticket_update_data}")
        
        def update_ticket():
            return requests.put(
                f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                json=ticket_update_data
            )
            
        ticket_response = retry_with_backoff(update_ticket)
        
        if ticket_response.status_code != 200:
            print(f"Failed to update ticket. Status: {ticket_response.status_code}")
            print(f"Response: {ticket_response.text}")
        else:
            print("Ticket updated successfully")
            
            def verify_ticket():
                return requests.get(f"{TICKET_SERVICE_URL}/tickets/{ticket_id}")
                
            verify_response = retry_with_backoff(verify_ticket)
            if verify_response.status_code == 200:
                updated_ticket = verify_response.json()
                print(f"Verified ticket status: {updated_ticket.get('status')}")
                print(f"Verified owner_id: {updated_ticket.get('owner_id')}")
            else:
                print("Warning: Could not verify ticket update")

        # Get event name from ticket details
        event_name = ticket_details.get("event_name", "Event")

        # Send success notifications
        notification_sent = send_transfer_success_notification(
            sender_email=data.get("sender_email"),
            recipient_email=data.get("recipient_email"),
            ticket_id=ticket_id,
            event_name=event_name
        )
        print(f"Notification sent: {notification_sent}")

        print("=== End Transfer Completion Debug ===\n")
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
        print(f"Error in transfer_ticket: {str(e)}")
        # In case of error, attempt to reset ticket status
        try:
            print("Attempting to reset ticket status...")
            def reset_ticket():
                return requests.put(
                    f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                    json={
                        "status": "SOLD",
                        "pending_transfer_to": None
                    }
                )
                
            retry_with_backoff(reset_ticket)
        except Exception as reset_error:
            print(f"Failed to reset ticket status: {str(reset_error)}")
            
        return jsonify({
            "error": "Transfer service error",
            "message": str(e)
        }), 500


def send_transfer_success_notification(sender_email, recipient_email, ticket_id, event_name):
    try:
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host='host.docker.internal', 
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
