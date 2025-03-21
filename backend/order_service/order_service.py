from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
import os
import certifi
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Flask App Initialization
app = Flask(__name__)
CORS(app)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://elijahtan2023:TXFgo2T6kEvD9pPh@esd.t8r4e.mongodb.net/esd"
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Service URL
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000")

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
    orders = list(orders_collection.find({"userId": user_id}))
    for order in orders:
        order["_id"] = str(order["_id"])
    return jsonify(orders)

###  Create a New Order (For Purchase) for User ID
@app.route("/orders/user/<string:user_id>", methods=["POST"])
def create_order_for_user(user_id):
    data = request.json

    # Validate Request Data
    required_fields = ["ticketIds", "eventId", "orderType", "totalAmount", "paymentId"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Generate Auto-Incrementing Order ID
    order_id = get_next_order_id()

    # Insert Order into Database
    new_order = {
        "orderId": order_id,
        "userId": user_id,
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
        "userId": user_id,
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

    # Update Order Status / Amount
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
        update_fields["refundDetails"] = {
            "sellerId": seller_id,
            "ticketId": ticket_id,
            "refundAmount": refund_amount,
            "paymentId": payment_id,
            "refundProcessedAt": datetime.utcnow()
        }
        update_fields["status"] = "RESOLD"

    # Apply Updates
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

    required_fields = ["ticketId", "fromEmail", "toEmail"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    from_email = data["fromEmail"]
    to_email = data["toEmail"]

    from_user_resp = requests.get(f"{USER_SERVICE_URL}/user/email/{from_email}")
    to_user_resp = requests.get(f"{USER_SERVICE_URL}/user/email/{to_email}")

    print(from_user_resp.json())
    print(to_user_resp.json())
    if from_user_resp.status_code != 200 or to_user_resp.status_code != 200:
        return jsonify({"error": "One or both users not found"}), 404

    from_user_id = from_user_resp.json().get("user_id")
    to_user_id = to_user_resp.json().get("user_id")
    print("FROM_USER_ID", from_user_id)
    print("TO_USER_ID", to_user_id)
    

    order = orders_collection.find_one({"userId": from_user_id, "ticketIds": {"$in": [data["ticketId"]]}})
    if not order:
        return jsonify({"error": "Original order not found for ticket transfer"}), 404

    # Remove the ticket from the ticketIds array
    orders_collection.update_one(
        {"_id": order["_id"]},
        {"$pull": {"ticketIds": data["ticketId"]}}
    )

    # If the original order has no tickets left, delete it
    updated_order = orders_collection.find_one({"_id": order["_id"]})
    if not updated_order["ticketIds"]:
        orders_collection.delete_one({"_id": order["_id"]})

    # Create new order for the recipient
    order_id = get_next_order_id()
    transfer_order = {
        "orderId": order_id,
        "userId": to_user_id,
        "ticketIds": [data["ticketId"]],
        "eventId": order.get("eventId"),
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
        "fromEmail": from_email,
        "toEmail": to_email,
        "ticketId": data["ticketId"],
        "orderType": "TRANSFER",
        "status": "COMPLETED",
        "createdAt": transfer_order["createdAt"].isoformat()
    }), 201

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
