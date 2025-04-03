import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import requests
from services import refund_payment, send_transfer_notification
import pika
from urllib.parse import urlparse

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:5001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8003")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5003")

def get_user_email(user_id):
    """Get user's email from User Service"""
    try:
        # Corrected endpoint based on user_service.py code
        endpoint = f"{USER_SERVICE_URL}/user/{user_id}"
        logger.info(f"Attempting to get user email from: {endpoint}")
        
        response = requests.get(endpoint, timeout=5)
        if response.status_code == 200:
            user_data = response.json()
            if "email" in user_data:
                logger.info(f"Found user email: {user_data['email']}")
                return user_data["email"]
            else:
                logger.warning(f"User found but no email field. Available fields: {list(user_data.keys())}")
        else:
            logger.warning(f"User service returned status code: {response.status_code}")
            
        # If direct lookup fails, try email lookup as fallback
        # This is based on the /user/email/<email> endpoint in your user service
        fallback_endpoint = f"{USER_SERVICE_URL}/user/email/{user_id}"
        logger.info(f"Trying fallback email lookup: {fallback_endpoint}")
        
        fallback_response = requests.get(fallback_endpoint, timeout=5)
        if fallback_response.status_code == 200:
            return user_id  # In this case, user_id might already be an email
            
        # For testing/development: If the user service can't be reached,
        # use the hardcoded email from the MongoDB for that user
        if user_id == "67e112f67621910c18c99249":
            logger.info("Using hardcoded email for testing")
            return "yiywe196@gmail.com"
            
        return user_id  # Return the ID as a last resort - it might be an email
        
    except Exception as e:
        logger.error(f"Error getting user email: {str(e)}")
        # Return the user ID as a fallback (it might be an email in some cases)
        return user_id

def check_rabbitmq_connection():
    """Check if RabbitMQ is accessible"""
    try:
        # Parse RABBITMQ_URL
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672")
        parameters = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(parameters)
        connection.close()
        return True
    except Exception as e:
        logger.error(f"RabbitMQ connection check failed: {str(e)}")
        return False

@app.route("/refund", methods=["POST"])
def refund_user_ticket():
    """Process refund for a single resale ticket to its original seller"""
    data = request.json
    required_fields = ["ticket_id", "seller_id", "refund_amount"]

    # Step 1: Validate required fields
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Extract input data
    ticket_id = data["ticket_id"]
    seller_id = data["seller_id"]
    
    # Step 3: Validate refund amount
    try:
        refund_amount = float(data["refund_amount"])
        if refund_amount <= 0:
            return jsonify({"error": "Refund amount must be positive"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid refund amount format"}), 400
    
    logger.info(f"Processing refund for ticket {ticket_id} to seller {seller_id}, amount: ${refund_amount}")

    try:
        # Step 2: Find seller's order containing this ticket
        # Get all orders for the seller
        logger.info(f"Retrieving orders for seller {seller_id}")
        seller_orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders/user/{seller_id}", timeout=5)
        if seller_orders_response.status_code != 200:
            return jsonify({"error": "Failed to retrieve seller orders"}), seller_orders_response.status_code
        
        seller_orders = seller_orders_response.json()
        if not isinstance(seller_orders, list):
            return jsonify({"error": "Invalid seller orders data format"}), 500
        
        # Find the order containing this ticket
        seller_order = None
        cat_id = None
        
        for order in seller_orders:
            # Check in new schema (nested tickets array)
            if "tickets" in order:
                for ticket_group in order["tickets"]:
                    if "ticketIds" in ticket_group and ticket_id in ticket_group["ticketIds"]:
                        seller_order = order
                        cat_id = ticket_group.get("catId")
                        break
            # Check in old schema (flat ticketIds array)
            elif "ticketIds" in order and ticket_id in order["ticketIds"]:
                seller_order = order
                cat_id = order.get("catId")
                break
                
            if seller_order:
                break
        
        if not seller_order:
            logger.error(f"Ticket {ticket_id} not found in any of seller {seller_id}'s orders")
            return jsonify({"error": "Ticket not found in seller's orders"}), 404
        
        order_id = seller_order.get("orderId")
        logger.info(f"Found ticket in order {order_id} with catId: {cat_id}")
        
        # Extract payment ID from the order
        payment_id = seller_order.get("paymentId")
        if not payment_id:
            return jsonify({"error": "Payment ID not found in order"}), 400
            
        # Step 4: Process payment refund
        logger.info(f"Processing payment refund of ${refund_amount} for payment {payment_id}")
        refund_response, refund_status = refund_payment(payment_id, refund_amount)
        if refund_status != 200:
            return jsonify(refund_response), refund_status

        refund_id = refund_response.get("refund_id")
        if not refund_id:
            return jsonify({
                "error": "Payment service returned invalid refund ID",
                "response": refund_response
            }), 500
        
        logger.info(f"Refund processed successfully with ID {refund_id}")

        # Step 5: Update seller's order - move ticket from ticketIds to refunded_ticket_ids
        logger.info(f"Updating order {order_id} - moving ticket to refunded_ticket_ids")
        
        # Create a copy of the order to modify
        updated_order = seller_order.copy()
        
        # Ensure _id is properly serialized if it exists
        if "_id" in updated_order:
            updated_order["_id"] = str(updated_order["_id"])
        
        # Handle removal of ticket from order based on schema
        ticket_removed = False
        
        # For new schema with nested tickets
        if "tickets" in updated_order:
            for ticket_group in updated_order["tickets"][:]:  # Create a copy for safe iteration
                if "ticketIds" in ticket_group and ticket_id in ticket_group["ticketIds"]:
                    ticket_group["ticketIds"].remove(ticket_id)
                    ticket_removed = True
                    # Update cat_id if not already set
                    if not cat_id and "catId" in ticket_group:
                        cat_id = ticket_group["catId"]
                    # If no more tickets in this group, remove the group
                    if not ticket_group["ticketIds"]:
                        updated_order["tickets"].remove(ticket_group)
                    break
        # For old schema with flat ticketIds array
        elif "ticketIds" in updated_order and ticket_id in updated_order["ticketIds"]:
            updated_order["ticketIds"].remove(ticket_id)
            ticket_removed = True
            # Update cat_id if not already set
            if not cat_id and "catId" in updated_order:
                cat_id = updated_order["catId"]
            
        if not ticket_removed:
            logger.warning(f"Ticket {ticket_id} not found in order structure for removal")
        
        # Add ticket to refunded_ticket_ids with the same nested structure as tickets
        if "refunded_ticket_ids" not in updated_order:
            updated_order["refunded_ticket_ids"] = []
        
        # Ensure we have a catId for the ticket
        if not cat_id:
            # Try to get it from ticket service as a fallback
            try:
                ticket_response = requests.get(f"{TICKET_SERVICE_URL}/tickets/{ticket_id}", timeout=5)
                if ticket_response.status_code == 200:
                    ticket_data = ticket_response.json()
                    cat_id = ticket_data.get("cat_id") or ticket_data.get("catId")
                    logger.info(f"Retrieved catId {cat_id} from ticket service")
            except Exception as e:
                logger.warning(f"Failed to get catId from ticket service: {str(e)}")
                
        # If still no catId, use a default
        if not cat_id:
            cat_id = "unknown"
            logger.warning(f"Using default catId '{cat_id}' for ticket {ticket_id}")
        
        # Check if this ticket is already in refunded_ticket_ids to avoid duplicates
        ticket_already_refunded = False
        for refund_group in updated_order["refunded_ticket_ids"]:
            if isinstance(refund_group, dict) and "ticketIds" in refund_group:
                if ticket_id in refund_group["ticketIds"]:
                    ticket_already_refunded = True
                    logger.warning(f"Ticket {ticket_id} already in refunded_ticket_ids")
                    break
            elif refund_group == ticket_id:  # Handle flat array case
                ticket_already_refunded = True
                logger.warning(f"Ticket {ticket_id} already in refunded_ticket_ids (flat array)")
                break
        
        if not ticket_already_refunded:
            # Use matching format with catId and nested ticketIds array
            cat_id_str = str(cat_id)  # Ensure catId is a string
            
            # Try to find an existing group with the same catId
            existing_group = None
            for group in updated_order["refunded_ticket_ids"]:
                if isinstance(group, dict) and group.get("catId") == cat_id_str:
                    existing_group = group
                    break
            
            if existing_group:
                # Add to existing group
                if "ticketIds" not in existing_group:
                    existing_group["ticketIds"] = []
                existing_group["ticketIds"].append(ticket_id)
                logger.info(f"Added ticket {ticket_id} to existing refunded group for catId {cat_id_str}")
            else:
                # Create new group
                updated_order["refunded_ticket_ids"].append({
                    "catId": cat_id_str,
                    "ticketIds": [ticket_id]
                })
                logger.info(f"Created new refunded group for catId {cat_id_str} with ticket {ticket_id}")
        
        # Add refund details
        if "refunds" not in updated_order:
            updated_order["refunds"] = []
        
        updated_order["refunds"].append({
            "ticket_id": ticket_id,
            "refund_id": refund_id,
            "amount": refund_amount,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Log the order update
        logger.info(f"Sending updated order to Order Service: {updated_order}")
        
        # Update the order - send the entire updated order object
        order_update_response = requests.put(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            json=updated_order,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if order_update_response.status_code != 200:
            # Attempt refund rollback if possible
            logger.error(f"Order update failed: {order_update_response.text}")
            try:
                requests.delete(f"{PAYMENT_SERVICE_URL}/payments/refund/{refund_id}")
                logger.info(f"Initiated rollback for refund {refund_id}")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {str(rollback_error)}")
                
            return jsonify({
                "error": "Order update failed after successful payment refund",
                "details": order_update_response.text,
                "refund_id": refund_id  # Include for possible manual reconciliation
            }), order_update_response.status_code

        # Step 6: Send notification to seller
        logger.info(f"Starting notification process for seller {seller_id}")
        seller_email = get_user_email(seller_id)
        logger.info(f"Retrieved seller email: {seller_email}")

        if seller_email:
            # Log the notification payload for debugging
            notification_payload = {
                "user_email": seller_email,
                "message": f"Your refund of ${refund_amount:.2f} for ticket {ticket_id} has been processed",
                "event_type": "ticket.refund.complete",
                "ticket_number": ticket_id,
                "amount": refund_amount,
                "event_name": "Ticket Refund"
            }
            logger.info(f"Attempting to send notification with payload: {notification_payload}")
            
            notification_sent = send_transfer_notification(**notification_payload)
            logger.info(f"Notification send result: {notification_sent}")
        else:
            logger.error(f"Could not send notification: email not found for user {seller_id}")
            notification_sent = False
        
        # Step 7: Return success response
        return jsonify({
            "message": "Refund to seller processed successfully",
            "refund_id": refund_id,
            "ticket_id": ticket_id,
            "seller_id": seller_id,
            "amount_refunded": refund_amount,
            "notification_sent": notification_sent
        }), 200
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during refund process: {str(e)}")
        return jsonify({"error": f"Service communication error: {str(e)}"}), 503
    except Exception as e:
        logger.error(f"Unexpected error during refund process: {str(e)}")
        return jsonify({"error": f"Refund processing failed: {str(e)}"}), 500

# Route for health check
@app.route("/health", methods=["GET"])
def health_check():
    rabbitmq_status = "connected" if check_rabbitmq_connection() else "disconnected"
    return jsonify({
        "status": "healthy",
        "service": "refund_user",
        "rabbitmq": rabbitmq_status
    }), 200

# Main entry point
if __name__ == "__main__":
    print("Starting Refund User Microservice on port 5005...")
    app.run(debug=True, host="0.0.0.0", port=5004)