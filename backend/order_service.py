from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
import os
import requests
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask App Initialization
app = Flask(__name__)

# ✅ MongoDB Configuration (Same as Other Microservices)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://elijahtan2023:TXFgo2T6kEvD9pPh@esd.t8r4e.mongodb.net/esd")
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Collection References
orders_collection = mongo.db.orders

# External Microservices URLs
USER_SERVICE_URL="http://localhost:5000"
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:5002")
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://localhost:5003")

# Helper Function to Convert ObjectId to String
def convert_objectid(obj):
    obj["_id"] = str(obj["_id"])
    return obj

# ✅ Retrieve an Order by ID
@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    try:
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if order:
            return jsonify(convert_objectid(order))
        return jsonify({"error": "Order not found"}), 404
    except:
        return jsonify({"error": "Invalid Order ID"}), 400

# ✅ Create or Retrieve an Order (Uses REST API Calls)
@app.route("/orders/create_or_retrieve", methods=["POST"])
def create_or_retrieve_order():
    """
    1. If order_id exists, retrieve the order.
    2. Otherwise, create a new order by fetching user_id, ticket_id, and payment details via REST API.
    """
    data = request.json
    order_id = data.get("order_id")

    # 1️⃣ **Check if Order Exists**
    if order_id:
        existing_order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if existing_order:
            return jsonify(convert_objectid(existing_order))

    # 2️⃣ **Fetch User Details via REST API**
    user_id = data.get("user_id")
    if not user_id:
        user_email = data.get("user_email")
    if not user_email:
        return jsonify({"error": "Missing user_email"}), 400

    user_response = requests.get(f"{USER_SERVICE_URL}/user/email/{user_email}") # Updated endpoint

    if user_response.status_code != 200:
        return jsonify({"error": "User not found"}), 404

    user_data = user_response.json()
    user_id = user_data.get("_id")  # Ensure this matches the API response field

    # 3️⃣ **Fetch Ticket Details via REST API**
    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"error": "Missing event_id"}), 400

    ticket_response = requests.get(f"{TICKET_SERVICE_URL}/tickets/event/{event_id}")
    if ticket_response.status_code != 200:
        return jsonify({"error": "Tickets not available"}), 404

    ticket_data = ticket_response.json()
    ticket_id = ticket_data.get("ticket_id")
    ticket_price = ticket_data.get("price")  # Assume ticket price is needed for payment

    # 4️⃣ **Process Payment via REST API**
    payment_payload = {
        "user_id": user_id,
        "amount": ticket_price,
    }
    payment_response = requests.post(f"{PAYMENT_SERVICE_URL}/payments/process", json=payment_payload)
    if payment_response.status_code != 200:
        return jsonify({"error": "Payment failed"}), 400

    payment_info = payment_response.json()
    payment_id = payment_info.get("payment_id")

    # 5️⃣ **Create the New Order**
    new_order = {
        "user_id": user_id,
        "ticket_id": ticket_id,
        "payment_id": payment_id,
        "amount": ticket_price,
        "status": "PENDING"
    }
    inserted_order = orders_collection.insert_one(new_order)

    return jsonify({
        "message": "Order created successfully",
        "order_id": str(inserted_order.inserted_id),
        "user_id": user_id,
        "ticket_id": ticket_id,
        "payment_id": payment_id,
        "amount": ticket_price,
        "status": "PENDING"
    }), 201

# ✅ Health Check API
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "Order Service is running"}), 200

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
