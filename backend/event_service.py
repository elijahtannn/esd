from flask import Flask, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Connect to MongoDB Atlas
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
event_collection = mongo.db.events  # MongoDB collection


# Route to get all events
@app.route("/events", methods=["GET"])
def get_events():
    events = list(event_collection.find({}, {"_id": 1, "description": 1, "dateTime": 1, "venue": 1, "type": 1}))

    # Convert MongoDB ObjectId to string
    for event in events:
        event["eventId"] = str(event["_id"])
        del event["_id"]  

    return jsonify(events), 200



if __name__ == "__main__":
    app.run(debug=True)  
