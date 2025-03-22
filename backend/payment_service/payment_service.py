from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import stripe
import os
import certifi
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# ✅ MongoDB Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://your_mongo_user:your_password@cluster.mongodb.net/payments")
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Collection Reference
payments_collection = mongo.db.payments

# ✅ Stripe API Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Make sure your .env file contains this

# 🔹 **Process Payment**
@app.route("/payments/process", methods=["POST"])
def process_payment():
    data = request.json
    try:
        required_fields = ["user_id", "amount", "payment_token"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # ✅ Use the token to create a charge
        charge = stripe.Charge.create(
            amount=int(data["amount"] * 100),  # cents
            currency="usd",
            source=data["payment_token"],
            description=f"Payment for user {data['user_id']}"
        )

        # ✅ Extract card details from the charge object
        card = charge["payment_method_details"]["card"]
        card_info = {
            "brand": card.get("brand"),
            "last4": card.get("last4"),
            "exp_month": card.get("exp_month"),
            "exp_year": card.get("exp_year"),
            "fingerprint": card.get("fingerprint")
        }

        # ✅ Store in MongoDB
        payment_record = {
            "user_id": data["user_id"],
            "amount": data["amount"],
            "payment_id": charge["id"],
            "status": "SUCCESS" if charge["paid"] else "FAILED",
            "card_info": card_info,
            "createdAt": datetime.utcnow()
        }
        payments_collection.insert_one(payment_record)

        return jsonify({
            "message": "Payment successful",
            "transaction_id": charge["id"],
            "amount": data["amount"],
            "status": "SUCCESS",
            "card": {
                "brand": card["brand"],
                "last4": card["last4"],
                "exp_month": card["exp_month"],
                "exp_year": card["exp_year"]
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400



# 🔹 **Process Refund**
@app.route("/payments/refund", methods=["POST"])
def process_refund():
    data = request.json
    try:
        # Validate Input
        required_fields = ["payment_id", "amount"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Retrieve payment record from DB
        payment = payments_collection.find_one({"payment_id": data["payment_id"]})
        if not payment:
            return jsonify({"error": "Payment record not found"}), 404

        # Process Refund via Stripe
        refund = stripe.Refund.create(
            charge=data["payment_id"],
            amount=int(data["amount"] * 100)  # Convert to cents
        )

        # Update Payment Status in MongoDB
        payments_collection.update_one(
            {"payment_id": data["payment_id"]},
            {"$set": {"status": "REFUNDED", "refund_id": refund["id"], "refundAt": datetime.utcnow()}}
        )

        return jsonify({
            "message": "Refund successful",
            "refund_id": refund["id"],
            "amount": data["amount"],
            "status": "REFUNDED"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=True)
