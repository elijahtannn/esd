from flask import Flask, redirect, url_for, jsonify, request
from flask_pymongo import PyMongo
import requests
import os
from datetime import datetime
from bson import ObjectId  
from flask_cors import CORS
import certifi
import json
import base64

app = Flask(__name__)
CORS(app)

# Secret Key for Sessions
app.secret_key = os.getenv("SECRET_KEY", "supersecurekey")


#New MongoDB Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app, tlsCAFile=certifi.where())

# Google OAuth Credentials
GOOGLE_CLIENT_ID = "603980424659-jiqs010nggvjmn6ve8c243nfral3q5a7.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Add this near the top of your file with other constants
KONG_URL = "http://localhost:8000"  # The public-facing Kong URL

# Fetch Google's OpenID Config
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# Route to Start Login
@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Use Kong's URL for the redirect_uri
    kong_callback_url = f"{KONG_URL}/login/callback"
    
    request_uri = (
        f"{authorization_endpoint}?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={kong_callback_url}"
        f"&response_type=code&scope=openid%20email%20profile"
    )
    return redirect(request_uri)

    
@app.route("/login/callback")
def callback():
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    
    auth_code = request.args.get("code")

    
    token_response = requests.post(
        token_endpoint,
        data={
            "code": auth_code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{KONG_URL}/login/callback",  # Use Kong URL here too
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return jsonify({"error": "Failed to retrieve access token"}), 401

    # Get user info from Google's API
    user_info_response = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    user_info = user_info_response.json()

    if "email" in user_info:
        user_email = user_info["email"]
        user_name = user_info.get("name", "")
        google_id = user_info.get("sub", "")

        # Check if user already exists
        users_collection = mongo.db.users
        existing_user = users_collection.find_one({"email": user_email})

        if not existing_user:
            new_user = {
                "name": user_name,
                "email": user_email,
                "mobile": "",
                "createdAt": datetime.now(),
                "google_id": google_id
            }
            insert_result = users_collection.insert_one(new_user)
            user_id = str(insert_result.inserted_id)
        else:
            user_id = str(existing_user["_id"])

        # Create user object for frontend
        user_data = {
            "id": user_id,
            "email": user_email,
            "name": user_name
        }

        # Redirect to frontend with encoded user data
        frontend_url = "http://localhost:5173"
        return redirect(f"{frontend_url}/?auth={base64.b64encode(json.dumps(user_data).encode()).decode()}")

    return jsonify({"error": "Authentication failed"}), 401

#GET: Fetch User by MongoDB `_id`
@app.route("/user/<string:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            return jsonify(user)
        return jsonify({"error": "User not found"}), 404
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400

#GET: Check if email exists in database
@app.route("/user/email/<email>", methods=["GET"])
def check_email(email):
    try:
        user = mongo.db.users.find_one({"email": email})
        if user:
            return jsonify({
                "exists": True,
                "user_id": str(user["_id"]),
                "email": user["email"]
            }), 200
        return jsonify({
            "exists": False,
            "message": "Email not found"
        }), 404
    except Exception as e:
        return jsonify({
            "error": "Database error",
            "message": str(e)
        }), 500

#PUT: Update user's mobile number and name
@app.route("/user/<string:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        
        data = request.get_json()
        
        
        update_fields = {}
        if "mobile" in data:
            update_fields["mobile"] = data["mobile"]
        if "name" in data:
            update_fields["name"] = data["name"]
            
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        
        result = mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )

        if result.modified_count == 0:
            return jsonify({"error": "User not found or no changes made"}), 404

        
        updated_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"]) 
        return jsonify(updated_user), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to update user",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003, debug=True)
