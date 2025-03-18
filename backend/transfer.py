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
ORDER_SERVICE_URL = "http://localhost:8000"
TICKET_SERVICE_URL = "http://127.0.0.1:5001"
VALIDATE_SERVICE_URL = "http://localhost:8004"
USER_SERVICE_URL = "http://localhost:5000"

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
            return jsonify({
                "error": "Transfer not accepted",
                "message": "Recipient must accept the transfer to proceed"
            }), 400

        # Get recipient's user ID from email using correct endpoint
        recipient_email = data.get('recipient_email')
        recipient_response = requests.get(
            f"{USER_SERVICE_URL}/user/email/{recipient_email}"
        )
        
        # Add debug logging
        print("User Service Response Status:", recipient_response.status_code)
        print("User Service Response Body:", recipient_response.text)
        
        if recipient_response.status_code != 200:
            return jsonify({
                "error": "Invalid recipient",
                "message": f"Could not find user with email {recipient_email}"
            }), 400
            
        recipient_data = recipient_response.json()
        print("Parsed recipient data:", recipient_data)
        
        # Get user_id from the response
        recipient_id = recipient_data.get("user_id")

        if not recipient_id:
            return jsonify({
                "error": "User data error",
                "message": "Could not get user ID from response"
            }), 400

        # Revalidate the transfer
        validation_response = requests.post(
            f"{VALIDATE_SERVICE_URL}/validateTransfer/{ticket_id}",
            json={
                "senderEmail": data.get("sender_email"),
                "recipientEmail": recipient_email
            }
        ).json()
        
        if not validation_response.get("can_transfer", False):
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
        
        # Update ticket ownership in Ticket Service
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
        return jsonify({
            "error": "Transfer service error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="localhost", port=8005, debug=True)
