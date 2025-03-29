from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
import os
import certifi
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info(f"Attempting to fetch orders for user: {user_id}")
        
        orders = list(orders_collection.find({"userId": user_id}))
        logger.info(f"Found {len(orders)} orders")
        
        for order in orders:
            order["_id"] = str(order["_id"])
        
        return jsonify(orders)
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return jsonify({"error": str(e)}), 500

### Create a New Order (Atomic Microservice)
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json

    # Now require "tickets" as a nested array
    required_fields = ["userId", "tickets", "eventId", "eventDateId", "orderType", "totalAmount", "paymentId"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        event_id = int(data["eventId"])
        event_date_id = int(data["eventDateId"])
        tickets = data["tickets"]  # Must be a list of nested ticket objects
        if not isinstance(tickets, list):
            raise ValueError("tickets must be a list")
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400

    order_id = get_next_order_id()

    new_order = {
        "orderId": order_id,
        "userId": data["userId"],
        "tickets": tickets,  # Nested array, e.g. [{"catId": "14", "ticketIds": ["id1"]}, {"catId": "13", "ticketIds": ["id2"]}]
        "eventId": event_id,
        "eventDateId": event_date_id,
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
        "tickets": tickets,
        "eventId": data["eventId"],
        "eventDateId": data["eventDateId"],
        "orderType": data["orderType"],
        "totalAmount": data["totalAmount"],
        "paymentId": data["paymentId"],
        "status": "COMPLETED",
        "createdAt": new_order["createdAt"].isoformat()
    }), 201

### Update Order (Including Refund Processing & Resale)
@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    data = request.json
    logger.info(f"Updating order {order_id} with data: {data}")
    
    order = orders_collection.find_one({"orderId": order_id})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # Handle complete order replacement (used by refund service)
    if "refunded_ticket_ids" in data or "refunds" in data:
        logger.info(f"Processing refund update for order {order_id}")
        # Remove the MongoDB _id since it can't be modified
        if "_id" in data:
            del data["_id"]
        
        # Update the entire order document with the new version
        result = orders_collection.replace_one({"orderId": order_id}, data)
        
        if result.modified_count > 0:
            logger.info(f"Successfully updated order {order_id} with refund details")
            return jsonify({
                "message": "Order updated successfully with refund details",
                "orderId": order_id
            })
        else:
            logger.warning(f"Order update failed: {order_id}")
            return jsonify({"error": "Order update failed"}), 500
    
    # Handle partial updates (original behavior)
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

    result = orders_collection.update_one({"orderId": order_id}, {"$set": update_fields})
    
    if result.modified_count > 0:
        return jsonify({
            "message": "Order updated successfully",
            "orderId": order_id,
            "updatedFields": update_fields
        })
    else:
        return jsonify({"error": "Order update failed"}), 500

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

    # Handle new order schema with nested tickets
    order = None
    
    # Try to find order with new schema (nested tickets)
    for doc in orders_collection.find({"userId": from_user_id}):
        if "tickets" in doc:
            for ticket_group in doc["tickets"]:
                if "ticketIds" in ticket_group and ticket_id in ticket_group["ticketIds"]:
                    order = doc
                    break
        if order:
            break
    
    # If not found, try old schema
    if not order:
        order = orders_collection.find_one({"userId": from_user_id, "ticketIds": {"$in": [ticket_id]}})
        
    if not order:
        return jsonify({"error": "Original order not found for ticket transfer"}), 404

    # Handle ticket removal based on schema
    if "tickets" in order:
        # New schema - find the correct ticket group
        for ticket_group in order["tickets"]:
            if "ticketIds" in ticket_group and ticket_id in ticket_group["ticketIds"]:
                orders_collection.update_one(
                    {"_id": order["_id"]},
                    {"$pull": {f"tickets.$[elem].ticketIds": ticket_id}},
                    array_filters=[{"elem.ticketIds": {"$in": [ticket_id]}}]
                )
                break
    else:
        # Old schema
        orders_collection.update_one({"_id": order["_id"]}, {"$pull": {"ticketIds": ticket_id}})

    # Check if order has any tickets left
    updated_order = orders_collection.find_one({"_id": order["_id"]})
    is_empty = True
    
    if "tickets" in updated_order:
        for group in updated_order["tickets"]:
            if "ticketIds" in group and group["ticketIds"]:
                is_empty = False
                break
    elif "ticketIds" in updated_order and updated_order["ticketIds"]:
        is_empty = False
        
    if is_empty:
        orders_collection.delete_one({"_id": order["_id"]})

    # Create new transfer order
    order_id = get_next_order_id()
    transfer_order = {
        "orderId": order_id,
        "userId": to_user_id,
        "tickets": [{"catId": data["catId"], "ticketIds": [ticket_id]}],  # Use new schema
        "eventId": data["eventId"],
        "eventDateId": data["eventDateId"],
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