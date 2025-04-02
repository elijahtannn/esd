from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import os
import pika
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class Config:
    TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:5001")
    OUTSYSTEMS_EVENT_API_URL = os.getenv("OUTSYSTEMS_EVENT_API_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5003")
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
    EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "ticketing.exchange")
    EXCHANGE_TYPE = os.getenv("EXCHANGE_TYPE", "topic")

# Service functions
def get_ticket_details(ticket_id):
    """Fetch ticket details from Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"
    response = requests.get(url)
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from Ticket Service"}
    return response_data, response.status_code

def get_event_details(event_id):
    """Fetch event details from Event Service"""
    url = f"{Config.OUTSYSTEMS_EVENT_API_URL}/events/{event_id}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from Event Service"}
    return response_data, response.status_code

def update_ticket_status(ticket_id):
    """Update ticket status to 'RESALE' in Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"
    payload = {"status": "RESALE"}
    response = requests.put(url, json=payload)
    return response.json(), response.status_code

def update_event_inventory(cat_id, resale_count):
    """Update event inventory in OutSystems Event Service"""
    url = f"{Config.OUTSYSTEMS_EVENT_API_URL}/events/dates/categories/{cat_id}/inventory/resale"
    headers = {"Content-Type": "application/json"}
    payload = {"Count": resale_count}
    response = requests.put(url, json=payload, headers=headers)
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from OutSystems"}
    return response_data, response.status_code

def get_interested_users(event_id):
    """Fetch users interested in an event from User Service"""
    url = f"{Config.USER_SERVICE_URL}/events/{event_id}/interested-users"
    response = requests.get(url)
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from User Service"}
    return response_data.get("users", []), response.status_code

# RabbitMQ Publisher
class RabbitMQPublisher:
    def __init__(self):
        self.rabbitmq_url = Config.RABBITMQ_URL
        self.exchange_name = Config.EXCHANGE_NAME
        self.exchange_type = Config.EXCHANGE_TYPE

    def _create_connection(self):
        if self.rabbitmq_url.startswith('amqp://'):
            credentials_url = self.rabbitmq_url[7:]
            if '@' in credentials_url:
                credentials, host_port = credentials_url.split('@')
                username, password = credentials.split(':')
            else:
                host_port = credentials_url
                username, password = 'guest', 'guest'
            
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host, port = host_port, 5672
            
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=pika.PlainCredentials(username, password)
            )
            return pika.BlockingConnection(parameters)
        return pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))

    def publish_message(self, routing_key, message):
        try:
            connection = self._create_connection()
            channel = connection.channel()
            
            channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type=self.exchange_type,
                durable=True
            )
            
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            
            connection.close()
            return True
        except Exception as e:
            print(f"Error publishing message: {str(e)}")
            return False

# Flask Application Setup
app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}})

resale_bp = Blueprint("resale_bp", __name__)
rabbitmq_publisher = RabbitMQPublisher()

@resale_bp.route("/resale/list", methods=["POST"])
def list_resale_ticket():
    """List a single ticket for resale"""
    data = request.json
    required_fields = ["ticket_id", "cat_id"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    ticket_id = data["ticket_id"]
    cat_id = data["cat_id"]
    
    # Optional: Get event_id from request if available, otherwise we'll get it from ticket details
    event_id = data.get("event_id")

    # Step 1: Get the current ticket details from Ticket Service
    ticket_details, ticket_status = get_ticket_details(ticket_id)

    if ticket_status != 200:
        return jsonify({"error": "Failed to retrieve ticket details", "details": ticket_details}), ticket_status

    current_status = ticket_details.get("status")
    
    # Get event_id from ticket details if not provided in request
    if not event_id and "event_id" in ticket_details:
        event_id = ticket_details["event_id"]

    # Step 2: Validate ticket status before allowing resale
    if current_status not in ["SOLD", "TRANSFERRED", "sold", "transferred"]:
        return jsonify({
            "error": f"Ticket cannot be listed for resale. Current status: {current_status}"
        }), 400
    
    # Step 3: Update event inventory in OutSystems Event Service
    inventory_response, inventory_status = update_event_inventory(cat_id, 1)
    
    # Check for errors in the inventory response
    if inventory_status != 200 or (isinstance(inventory_response, dict) and 
                                  inventory_response.get("Result") and 
                                  "ErrorMessage" in inventory_response["Result"]):
        error_message = inventory_response.get("Result", {}).get("ErrorMessage", "Unknown error")
        return jsonify({"error": "Failed to update event inventory", "details": error_message}), 400
    
    # Step 4: Only update ticket status if inventory update was successful
    ticket_response, ticket_status = update_ticket_status(ticket_id)
    if ticket_status != 200:
        return jsonify({"error": "Failed to update ticket status", "details": ticket_response}), ticket_status

    # Step 5: Gather event information and notify interested users
    print(f"DEBUG: Starting to gather event details for event_id: {event_id}")
    event_name = None
    event_details = {}

    if event_id:
        event_info, event_status = get_event_details(event_id)
        print(f"DEBUG: Event details status: {event_status}")
        print(f"DEBUG: Full event response: {event_info}")

        if event_status == 200:
            events_data = event_info.get("Event", [])
            
            if events_data:
                matched_event = next((event for event in events_data 
                                    if str(event.get("EventId")) == str(event_id) or 
                                       str(event.get("Id")) == str(event_id)), 
                                   events_data[0])
                
                event_name = matched_event.get("Name", "Event")
                event_details = {
                    "eventId": event_id,
                    "eventName": event_name,
                    "eventDate": matched_event.get("Date", ""),
                    "eventLocation": matched_event.get("Venue", ""),
                    "eventVenue": matched_event.get("Venue", ""),
                    "categoryName": matched_event.get("Category", "")
                }
                
                # Get interested users and send notifications
                interested_users, users_status = get_interested_users(event_id)
                if users_status == 200 and interested_users:
                    print(f"DEBUG: Found {len(interested_users)} interested users")
                    # Publish notification for each interested user
                    for user in interested_users:
                        notification_data = {
                            "eventType": "ticket.resale.available",
                            "email": user["email"],
                            "eventId": event_id,
                            "eventName": event_name,
                            "eventDate": event_details["eventDate"],
                            "eventLocation": event_details["eventLocation"],
                            "eventVenue": event_details["eventVenue"],
                            "categoryName": event_details["categoryName"]
                        }
                        print(f"DEBUG: Sending notification to {user['email']}")
                        rabbitmq_publisher.publish_message(
                            routing_key="ticket.resale.available",
                            message=notification_data
                        )
                        print(f"DEBUG: Notification sent to user {user['email']}")
                else:
                    print(f"DEBUG: No interested users found or error getting users. Status: {users_status}")
            else:
                print("DEBUG: No events found in the response")
        else:
            print(f"DEBUG: Failed to retrieve event details. Status: {event_status}")
            print(f"DEBUG: Response: {event_info}")
    
    return jsonify({
        "message": "Ticket listed for resale successfully",
        "ticket_update": ticket_response,
        "inventory_update": inventory_response
    }), 200

app.register_blueprint(resale_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)