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
    

# POST: Add an event to user's interested_events list
@app.route("/user/<string:user_id>/interested-events", methods=["POST"])
def add_interested_event(user_id):
    try:
        data = request.get_json()
        
        if not data or "event_id" not in data:
            return jsonify({"error": "Event ID is required"}), 400
        
        event_id = data["event_id"]
        
        # Check if user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if event is already in the user's interested_events list
        # Handle both string and integer event IDs
        is_already_interested = False
        interested_events = user.get("interested_events", [])
        
        for interested_event in interested_events:
            if str(interested_event) == str(event_id):
                is_already_interested = True
                break
                
        if is_already_interested:
            return jsonify({
                "message": "User is already subscribed to notifications for this event",
                "event_id": event_id
            }), 200
            
        # Add the event to the interested_events list
        # Decide whether to store as int or string based on what was passed
        try:
            # If it can be converted to an integer, store it that way for consistency
            if event_id.isdigit():
                event_id_to_store = int(event_id)
            else:
                event_id_to_store = event_id
        except (AttributeError, ValueError):
            # If conversion fails, store as is
            event_id_to_store = event_id
            
        result = mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"interested_events": event_id_to_store}}  # Use addToSet to avoid duplicates
        )
        
        if result.modified_count == 1:
            return jsonify({
                "message": "Event added to user's interested events",
                "event_id": event_id
            }), 201
        else:
            return jsonify({
                "message": "No changes made",
                "event_id": event_id
            }), 200
            
    except Exception as e:
        return jsonify({
            "error": "Failed to add event to interested events",
            "message": str(e)
        }), 500

# DELETE: Remove an event from user's interested_events list
@app.route("/user/<string:user_id>/interested-events/<string:event_id>", methods=["DELETE"])
def remove_interested_event(user_id, event_id):
    try:
        # Check if user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # We need to handle both integer and string event IDs
        # First, find the actual event ID format in the array
        interested_events = user.get("interested_events", [])
        target_event = None
        
        for interested_event in interested_events:
            if str(interested_event) == str(event_id):
                target_event = interested_event
                break
        
        if target_event is not None:
            # Remove the event from the interested_events list
            result = mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"interested_events": target_event}}
            )
            
            if result.modified_count == 1:
                return jsonify({
                    "message": "Event removed from user's interested events",
                    "event_id": event_id
                }), 200
            else:
                return jsonify({
                    "message": "Failed to remove event from user's interested events",
                    "event_id": event_id
                }), 500
        else:
            return jsonify({
                "message": "Event was not in user's interested events",
                "event_id": event_id
            }), 200
            
    except Exception as e:
        return jsonify({
            "error": "Failed to remove event from interested events",
            "message": str(e)
        }), 500

# GET: Get all events a user is interested in
@app.route("/user/<string:user_id>/interested-events", methods=["GET"])
def get_interested_events(user_id):
    try:
        # Check if user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Return the interested_events list
        interested_events = user.get("interested_events", [])
        return jsonify({
            "interested_events": interested_events,
            "count": len(interested_events)
        }), 200
            
    except Exception as e:
        return jsonify({
            "error": "Failed to get interested events",
            "message": str(e)
        }), 500

# GET: Check if user is interested in a specific event
@app.route("/user/<string:user_id>/interested-events/<string:event_id>", methods=["GET"])
def check_interested_event(user_id, event_id):
    try:
        # Check if user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if event is in interested_events list
        # Handle both string and integer event IDs
        interested_events = user.get("interested_events", [])
        is_interested = False
        
        # Convert both to strings for comparison
        for interested_event in interested_events:
            if str(interested_event) == str(event_id):
                is_interested = True
                break
                
        return jsonify({
            "is_interested": is_interested,
            "event_id": event_id
        }), 200
            
    except Exception as e:
        return jsonify({
            "error": "Failed to check interested event",
            "message": str(e)
        }), 500
    
# GET: Get all users interested in a specific event (for notification service)
@app.route("/events/<string:event_id>/interested-users", methods=["GET"])
def get_interested_users(event_id):
    try:
        # Convert event_id to int if it's a digit string for proper matching
        event_id_value = int(event_id) if event_id.isdigit() else event_id
        
        # Find all users who have this event in their interested_events list
        # We need to use $or to handle both string and integer event IDs
        users = list(mongo.db.users.find({
            "$or": [
                {"interested_events": event_id_value},
                {"interested_events": event_id}
            ]
        }))
        
        if not users:
            return jsonify({
                "message": "No users found interested in this event",
                "event_id": event_id,
                "users": []
            }), 200
            
        # Format user data for response
        user_list = []
        for user in users:
            user_list.append({
                "user_id": str(user["_id"]),
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "mobile": user.get("mobile", "")
            })
            
        return jsonify({
            "event_id": event_id,
            "users_count": len(user_list),
            "users": user_list
        }), 200
            
    except Exception as e:
        return jsonify({
            "error": "Failed to get interested users",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003, debug=True)
