from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
import os
import requests
import certifi
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# ✅ MongoDB Connection
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://elijahtan2023:TXFgo2T6kEvD9pPh@esd.t8r4e.mongodb.net/esd")
mongo = PyMongo(app, tlsCAFile=certifi.where())

# ✅ Stripe API Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ✅ Collection Reference
payments_collection = mongo.db.payments


### 🔹 **Helper Function: Call Stripe API**
def call_stripe_api(payment_data):
    """ Calls Stripe API to process payment. """
    try:
        charge = stripe.Charge.create(
            amount=int(payment_data["amount"] * 100),  # Convert dollars to cents
            currency="usd",
            source=payment_data["token"],  # Payment token from frontend
            description=f"Payment for Ticket {payment_data['ticket_id']}"
        )
        return charge
    except Exception as e:
        return {"error": str(e)}


### 🔹 **Process Payment API**
@app.route("/payments/process", methods=["POST"])
def process_payment():
    """
    Processes a payment by calling Stripe API.
    Stores transaction details in MongoDB.
    """
    data = request.json
    user_id = data.get("user_id")
    amount = data.get("amount")
    ticket_id = data.get("ticket_id")
    token = data.get("token")  # Payment token from frontend

    if not user_id or not amount or not ticket_id or not token:
        return jsonify({"error": "Missing required payment fields"}), 400

    # Call Stripe API
    charge = call_stripe_api(data)
    
    if "error" in charge:
        return jsonify({"error": charge["error"]}), 400

    # Store payment details in MongoDB
    payment_data = {
        "user_id": user_id,
        "ticket_id": ticket_id,
        "amount": amount,
        "status": "SUCCESS" if charge["paid"] else "FAILED",
        "transaction_id": charge["id"]
    }
    payments_collection.insert_one(payment_data)

    return jsonify({"message": "Payment successful", "transaction_id": charge["id"]})


### 🔹 **Refund Payment API**
@app.route("/payments/refund", methods=["POST"])
def refund_payment():
    """
    Refunds a payment by calling Stripe API.
    Updates MongoDB record to REFUNDED.
    """
    data = request.json
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"error": "Missing order_id"}), 400

    # Retrieve payment from database
    payment = payments_collection.find_one({"order_id": order_id})
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    # Call Stripe Refund API
    try:
        refund = stripe.Refund.create(charge=payment["transaction_id"])

        # Update payment status in MongoDB
        payments_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": "REFUNDED"}}
        )
        return jsonify({"message": "Refund successful", "refund_id": refund["id"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


### 🔹 **Get Payment Details API**
@app.route("/payments/<order_id>", methods=["GET"])
def get_payment(order_id):
    """
    Fetches payment details by order ID from MongoDB.
    """
    payment = payments_collection.find_one({"order_id": order_id})
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    
    payment["_id"] = str(payment["_id"])  # Convert ObjectId to string
    return jsonify(payment)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
