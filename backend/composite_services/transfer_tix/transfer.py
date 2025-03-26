from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv()

# Service URLs
ORDER_SERVICE_URL = "http://order-service:8003"
TICKET_SERVICE_URL = "http://ticket-service:5001"
VALIDATE_SERVICE_URL = "http://validate-service:8004"
USER_SERVICE_URL = "http://user-service:5003"

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
            # If rejected, update ticket status back to "sold"
            ticket_response = requests.put(
                f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                json={
                    "status": "sold"  # Reset status back to sold
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
                    "status": "sold"
                }
            )
            
            return jsonify({
                "error": "Validation failed",
                "message": validation_response.get("message", "Transfer conditions are no longer valid")
            }), 400

        # Create transfer order in Order Service
        order_response = requests.post(
            f"{ORDER_SERVICE_URL}/orders/transfer",
            json={
                "ticketId": ticket_id,
                "fromUserId": data.get("sender_id"),
                "toUserId": recipient_id
            }
        ).json()
        
        # Update ticket ownership and status in Ticket Service
        ticket_response = requests.put(
            f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
            json={
                "owner_id": recipient_id,
                "status": "transferred"
            }
        ).json()

        return jsonify({
            "success": True,
            "message": "Ticket transferred successfully",
            "transfer_details": {
                "ticket_id": ticket_id,
                "from_user_id": data.get("sender_id"),
                "to_user_id": recipient_id,
                "transfer_date": datetime.now().isoformat(),
                "order_id": order_response.get("orderId")
            }
        }), 200

    except Exception as e:
        # In case of error, attempt to reset ticket status
        try:
            requests.put(
                f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                json={"status": "sold"}
            )
        except:
            pass  # Ignore errors in cleanup
            
        return jsonify({
            "error": "Transfer service error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="localhost", port=8005, debug=True)
