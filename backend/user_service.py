from flask import Flask, redirect, url_for, jsonify, request
from flask_pymongo import PyMongo
import requests
import os
from datetime import datetime
from bson import ObjectId  

app = Flask(__name__)

# Secret Key for Sessions
app.secret_key = os.getenv("SECRET_KEY", "supersecurekey")

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://elijahtan2023:TXFgo2T6kEvD9pPh@esd.t8r4e.mongodb.net/esd?retryWrites=true&w=majority"
mongo = PyMongo(app)

# Google OAuth Credentials
GOOGLE_CLIENT_ID = "607054073148-6mpeml07e2asg4daka42en3l4iha33vm.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Fetch Google's OpenID Config
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# Route to Start Login
@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Redirect user to Google's OAuth 2.0 authentication
    request_uri = (
        f"{authorization_endpoint}?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={url_for('callback', _external=True)}"
        f"&response_type=code&scope=openid%20email%20profile"
    )
    return redirect(request_uri)

# OAuth Callback Route (Handles Google's Response)
@app.route("/login/callback")
def callback():
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Get authorization code from Google redirect
    auth_code = request.args.get("code")

    # Exchange authorization code for access token
    token_response = requests.post(
        token_endpoint,
        data={
            "code": auth_code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": url_for("callback", _external=True),
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
        google_id = user_info.get("sub", "")  # Google ID

        # Check if user already exists
        users_collection = mongo.db.users
        existing_user = users_collection.find_one({"email": user_email})

        if not existing_user:
            # Create new user with an empty mobile number
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

        return jsonify({"message": "Login successful", "user_id": user_id, "email": user_email})

    return jsonify({"error": "Authentication failed"}), 401

# ✅ GET: Fetch User by MongoDB `_id`
@app.route("/user/<string:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string
            return jsonify(user)
        return jsonify({"error": "User not found"}), 404
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400

if __name__ == "__main__":
    app.run(debug=True)
