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
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
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

### Get Orders by User ID
@app.route("/orders/user/<string:user_id>", methods=["GET"])
def get_orders_by_user(user_id):
    try:
        # Add print statements for debugging
        print(f"Attempting to fetch orders for user: {user_id}")
        
        orders = list(orders_collection.find({"userId": user_id}))
        print(f"Found {len(orders)} orders")
        
        for order in orders:
            order["_id"] = str(order["_id"])
        
        return jsonify(orders)
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return jsonify({"error": str(e)}), 500

### Create a New Order (Atomic Microservice)
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json

    required_fields = ["userId", "ticketIds", "eventId", "eventDateId", "catId", "orderType", "totalAmount", "paymentId"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Convert numeric fields to integers
    try:
        event_id = int(data["eventId"])
        event_date_id = int(data["eventDateId"])
        cat_id = int(data["catId"])
    except (ValueError, TypeError):
        return jsonify({"error": "eventId, eventDateId, and catId must be integers"}), 400

    order_id = get_next_order_id()

    new_order = {
        "orderId": order_id,
        "userId": data["userId"],
        "ticketIds": data["ticketIds"],
        "eventId": event_id,  # Use the converted integer
        "eventDateId": event_date_id,  # Use the converted integer
        "catId": cat_id,  # Use the converted integer
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
        "eventDateId": data["eventDateId"],
        "catId": data["catId"],
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

    data = request.json
    update_fields = {}

    for field in ["status", "totalAmount"]:
        if field in data:
            update_fields[field] = data[field]

    # Refund/resale info
    if all(k in data for k in ["sellerId", "ticketId", "refundAmount", "paymentId"]):
        update_fields["refundDetails"] = {
            "sellerId": data["sellerId"],
            "ticketId": data["ticketId"],
            "refundAmount": data["refundAmount"],
            "paymentId": data["paymentId"],
            "refundProcessedAt": datetime.utcnow()
        }
        update_fields["status"] = "RESOLD"

    orders_collection.update_one({"orderId": order_id}, {"$set": update_fields})

    return jsonify({
        "message": "Order updated successfully",
        "orderId": order_id,
        "updatedFields": update_fields
    })

### Transfer Ticket Using Emails
@app.route("/orders/transfer", methods=["POST"])
def transfer_ticket():
    data = request.json
    required_fields = ["ticketId", "fromUserId", "toUserId", "eventId", "eventDateId", "catId"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    from_user_id = data["fromUserId"]
    to_user_id = data["toUserId"]
    ticket_id = data["ticketId"]

    order = orders_collection.find_one({"userId": from_user_id, "ticketIds": {"$in": [ticket_id]}})
    if not order:
        return jsonify({"error": "Original order not found for ticket transfer"}), 404

    orders_collection.update_one({"_id": order["_id"]}, {"$pull": {"ticketIds": ticket_id}})

    updated_order = orders_collection.find_one({"_id": order["_id"]})
    if not updated_order["ticketIds"]:
        orders_collection.delete_one({"_id": order["_id"]})

    order_id = get_next_order_id()
    transfer_order = {
        "orderId": order_id,
        "userId": to_user_id,
        "ticketIds": [ticket_id],
        "eventId": data["eventId"],
        "eventDateId": data["eventDateId"],
        "catId": data["catId"],
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
        "ticketId": ticket_id,
        "fromUserId": from_user_id,
        "toUserId": to_user_id,
        "orderType": "TRANSFER",
        "status": "COMPLETED",
        "createdAt": transfer_order["createdAt"].isoformat()
    }), 201

# Add a simple health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    try:
        # Test MongoDB connection
        mongo.db.command('ping')
        return jsonify({"status": "healthy", "message": "Service is running and connected to MongoDB"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "message": str(e)}), 500


# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003, debug=True)
