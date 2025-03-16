from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
import os
import certifi
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask App Initialization
app = Flask(__name__)
CORS(app)

# MongoDB Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://elijahtan2023:TXFgo2T6kEvD9pPh@esd")
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Collection References
orders_collection = mongo.db.orders
counters_collection = mongo.db.counters  # Used for auto-incrementing `orderId`

### Auto-Increment Function for `orderId`
def get_next_order_id():
    counter = counters_collection.find_one_and_update(
        {"_id": "orderId"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return counter["seq"]

### Get Order Details
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """
    Retrieves an order by its `orderId`.
    """
    order = orders_collection.find_one({"orderId": order_id})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order["_id"] = str(order["_id"])  # Convert ObjectId to string
    return jsonify(order)

###  Create a New Order (For Purchase)
@app.route("/orders", methods=["POST"])
def create_order():

    data = request.json

    # Validate Request Data
    required_fields = ["userId", "ticketIds", "eventId", "orderType", "totalAmount", "paymentId"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Generate Auto-Incrementing Order ID
    order_id = get_next_order_id()

    # Insert Order into Database
    new_order = {
        "orderId": order_id,
        "userId": data["userId"],
        "ticketIds": data["ticketIds"],
        "eventId": data["eventId"],
        "orderType": data["orderType"],
        "totalAmount": data["totalAmount"],
        "paymentId": data["paymentId"],
        "status": "COMPLETED",
        "createdAt": datetime.utcnow()
    }
    orders_collection.insert_one(new_order)

    return jsonify({
        "message": "Order created successfully",
        "orderId": order_id,
        "userId": data["userId"],
        "ticketIds": data["ticketIds"],
        "eventId": data["eventId"],
        "orderType": data["orderType"],
        "totalAmount": data["totalAmount"],
        "paymentId": data["paymentId"],
        "status": "COMPLETED",
        "createdAt": new_order["createdAt"].isoformat()
    }), 201

### Update Order (Including Refund Processing & Resale)
@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_order(order_id):

    order = orders_collection.find_one({"orderId": order_id})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # Get update fields
    data = request.json
    update_fields = {}

    #Update Order Status / Amount
    if "status" in data:
        update_fields["status"] = data["status"]
    if "totalAmount" in data:
        update_fields["totalAmount"] = data["totalAmount"]

    # Handle Refund Processing
    seller_id = data.get("sellerId")
    ticket_id = data.get("ticketId")
    refund_amount = data.get("refundAmount")
    payment_id = data.get("paymentId")

    if all([seller_id, ticket_id, refund_amount, payment_id]):
        # Store refund details
        update_fields["refundDetails"] = {
            "sellerId": seller_id,
            "ticketId": ticket_id,
            "refundAmount": refund_amount,
            "paymentId": payment_id,
            "refundProcessedAt": datetime.utcnow()
        }
        update_fields["status"] = "RESOLD"  # Automatically mark status as refunded

    # Apply Updates
    orders_collection.update_one({"orderId": order_id}, {"$set": update_fields})

    return jsonify({
        "message": "Order updated successfully",
        "orderId": order_id,
        "updatedFields": update_fields
    })

### Transfer Ticket to Another User
@app.route("/orders/transfer", methods=["POST"])
def transfer_ticket():

    data = request.json

    # Validate Request Data
    required_fields = ["ticketId", "fromUserId", "toUserId"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Generate Auto-Incrementing Order ID for Transfer
    order_id = get_next_order_id()

    # Insert Transfer Order into Database
    transfer_order = {
        "orderId": order_id,
        "userId": data["toUserId"],  # New Ticket Owner
        "ticketIds": [data["ticketId"]],
        "eventId": None,  # Not required for transfers
        "orderType": "TRANSFER",
        "totalAmount": 0.0,
        "paymentId": None,
        "status": "TRANSFERRED",
        "createdAt": datetime.utcnow()
    }
    orders_collection.insert_one(transfer_order)

    return jsonify({
        "message": "Ticket transferred successfully",
        "orderId": order_id,
        "fromUserId": data["fromUserId"],
        "toUserId": data["toUserId"],
        "ticketId": data["ticketId"],
        "orderType": "TRANSFER",
        "status": "COMPLETED",
        "createdAt": transfer_order["createdAt"].isoformat()
    }), 201

### Health Check API
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "Order Service is running"}), 200

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
