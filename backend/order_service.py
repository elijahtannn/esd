from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
import os
import certifi
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask App Initialization
app = Flask(__name__)

# ✅ MongoDB Configuration (Atomic Microservice)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://elijahtan2023:TXFgo2T6kEvD9pPh@esd.t8r4e.mongodb.net/esd")
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Collection References
orders_collection = mongo.db.orders
counters_collection = mongo.db.counters  # Used for auto-incrementing `orderId`


### **🔹 Auto-Increment Function for `orderId`**
def get_next_order_id():
    counter = counters_collection.find_one_and_update(
        {"_id": "orderId"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return counter["seq"]


### **🔹 1️⃣ Get Order Details**
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


### **🔹 2️⃣ Create a New Order**
@app.route("/orders", methods=["POST"])
def create_order():
    """
    Creates a new order in the database.
    """
    data = request.json
    user_id = data.get("userId")
    ticket_ids = data.get("ticketIds")
    event_id = data.get("eventId")
    order_type = data.get("orderType")
    total_amount = data.get("totalAmount")
    payment_id = data.get("paymentId")
    status = data.get("status", "PENDING")  # Default status: PENDING

    # Validation
    if not all([user_id, ticket_ids, event_id, order_type, total_amount, payment_id]):
        return jsonify({"error": "Missing required fields"}), 400

    # Generate Auto-Incrementing Order ID
    order_id = get_next_order_id()

    # Insert into database
    new_order = {
        "orderId": order_id,
        "userId": user_id,
        "ticketIds": ticket_ids,
        "eventId": event_id,
        "orderType": order_type,
        "totalAmount": total_amount,
        "paymentId": payment_id,
        "status": status,
        "createdAt": datetime.utcnow()
    }
    orders_collection.insert_one(new_order)

    return jsonify({
        "message": "Order created successfully",
        "orderId": order_id,
        "userId": user_id,
        "ticketIds": ticket_ids,
        "eventId": event_id,
        "orderType": order_type,
        "totalAmount": total_amount,
        "paymentId": payment_id,
        "status": status,
        "createdAt": new_order["createdAt"].isoformat()
    }), 201


### **🔹 3️⃣ Update Order Details**
@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    """
    Updates an existing order.
    - If only `status` or `totalAmount` is updated, modify the order.
    - If refund details are provided, process refund and update order.
    """
    order = orders_collection.find_one({"orderId": order_id})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # Get update fields
    data = request.json
    update_fields = {}

    # ✅ Update Order Status / Amount
    if "status" in data:
        update_fields["status"] = data["status"]
    if "totalAmount" in data:
        update_fields["totalAmount"] = data["totalAmount"]

    # ✅ Handle Refund Processing
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
        update_fields["status"] = "REFUNDED"  # Automatically mark status as refunded

    # Apply Updates
    orders_collection.update_one({"orderId": order_id}, {"$set": update_fields})

    return jsonify({
        "message": "Order updated successfully",
        "orderId": order_id,
        "updatedFields": update_fields
    })


### **✅ Health Check API**
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "Order Service is running"}), 200


# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
