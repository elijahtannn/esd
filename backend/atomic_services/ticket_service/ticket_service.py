from flask import Flask, Blueprint, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import threading
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
CORS(app)

# Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/esd")

# Initialize MongoDB
mongo = PyMongo(app)

def get_ticket_collection():
    """Get the ticket collection from MongoDB"""
    return mongo.db.tickets

class Ticket:
    """Ticket Model"""

    def __init__(self, event_id, event_date_id, cat_id, owner_id, seat_info, status="available", is_transferable=True, qr_code=None):
        self.event_id = int(event_id)
        self.event_date_id = int(event_date_id)
        self.cat_id = int(cat_id)
        self.owner_id = owner_id
        self.seat_info = seat_info
        self.status = status
        self.is_transferable = is_transferable
        self.qr_code = qr_code if qr_code else ""
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert Ticket object to a dictionary for MongoDB storage"""
        return {
            "event_id": self.event_id,
            "event_date_id": self.event_date_id,
            "cat_id": self.cat_id,
            "owner_id": str(self.owner_id),
            "seat_info": self.seat_info,
            "status": self.status,
            "is_transferable": self.is_transferable,
            "qr_code": self.qr_code,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def serialize_ticket(ticket_dict):
        """Serialize a ticket dictionary from MongoDB to ensure JSON compatibility"""
        serialized = ticket_dict.copy()
        
        if "_id" in serialized:
            serialized["_id"] = str(serialized["_id"])
        if "owner_id" in serialized:
            serialized["owner_id"] = str(serialized["owner_id"])
        if "created_at" in serialized:
            serialized["created_at"] = serialized["created_at"].isoformat() if serialized["created_at"] else None
        if "updated_at" in serialized:
            serialized["updated_at"] = serialized["updated_at"].isoformat() if serialized["updated_at"] else None
        
        return serialized

# Create Blueprint
ticket_bp = Blueprint('ticket_bp', __name__)

def release_ticket_after_delay(ticket_ids, delay_seconds=180):
    def release():
        ticket_collection = get_ticket_collection()
        now = datetime.utcnow()
        expired_time = now - timedelta(seconds=delay_seconds)
        result = ticket_collection.delete_many({
            "_id": {"$in": [ObjectId(tid) for tid in ticket_ids]},
            "status": "RESERVED",
            "created_at": {"$lt": expired_time}
        })
        print(f"[Timer] Released and deleted {result.deleted_count} unconfirmed reserved ticket(s)")

    timer = threading.Timer(delay_seconds, release)
    timer.start()

@ticket_bp.route('/tickets/release', methods=['POST'])
def release_tickets():
    data = request.json
    ticket_ids = data.get("ticket_ids")
    owner_id = data.get("owner_id")

    if not ticket_ids or not owner_id:
        return jsonify({"error": "Missing ticket_ids or owner_id"}), 400

    try:
        result = get_ticket_collection().delete_many({
            "_id": {"$in": [ObjectId(tid) for tid in ticket_ids]},
            "owner_id": str(owner_id),
            "status": "RESERVED"
        })

        return jsonify({
            "message": f"Released and deleted {result.deleted_count} reserved ticket(s)",
            "ticket_ids": ticket_ids
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to release tickets: {str(e)}"}), 400

@ticket_bp.route('/tickets/reserve', methods=['POST'])
def create_tickets():
    data = request.json
    required_fields = ["event_id", "event_date_id", "cat_id", "owner_id", "seat_info", "qr_code"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        num_tickets = int(data.get("num_tickets", 1))
        if num_tickets <= 0:
            return jsonify({"error": "Number of tickets must be at least 1"}), 400

        tickets = []
        now = datetime.utcnow()
        for _ in range(num_tickets):
            ticket_dict = Ticket(
                event_id=int(data["event_id"]),
                event_date_id=int(data["event_date_id"]),
                cat_id=int(data["cat_id"]),
                owner_id=data["owner_id"],
                seat_info=data["seat_info"],
                status="RESERVED",
                is_transferable=data.get("is_transferable", True),
                qr_code=data.get("qr_code", "")
            ).to_dict()
            ticket_dict["created_at"] = now
            ticket_dict["updated_at"] = now
            tickets.append(ticket_dict)

        result = get_ticket_collection().insert_many(tickets)
        inserted_ids = [str(ticket_id) for ticket_id in result.inserted_ids]

        # Set up automatic ticket release timer
        release_ticket_after_delay(inserted_ids)

        return jsonify({
            "message": f"{num_tickets} ticket(s) reserved successfully",
            "ticket_ids": inserted_ids
        }), 201

    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400

@ticket_bp.route('/tickets/confirm', methods=['PUT'])
def confirm_ticket_purchase():
    """Confirm ticket purchase by updating status from 'reserved' to 'sold'"""
    data = request.json
    required_fields = ["ticket_ids"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        ticket_ids = []
        for tid in data["ticket_ids"]:
            try:
                ticket_ids.append(ObjectId(tid))
            except Exception:
                continue

        tickets = list(get_ticket_collection().find({"_id": {"$in": ticket_ids}}))
        
        if not tickets:
            return jsonify({"error": "No matching tickets found"}), 404

        reserved_ticket_ids = [t["_id"] for t in tickets if t["status"] == "RESERVED"]
        non_reserved = [str(t["_id"]) for t in tickets if t["status"] != "RESERVED"]

        if not reserved_ticket_ids:
            return jsonify({"error": "No tickets in 'RESERVED' state", "non_reserved": non_reserved}), 400

        result = get_ticket_collection().update_many(
            {"_id": {"$in": reserved_ticket_ids}},
            {"$set": {"status": "SOLD", "updated_at": datetime.utcnow()}}
        )

        return jsonify({
            "message": f"Successfully updated {result.modified_count} ticket(s) to 'SOLD'"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
   
@ticket_bp.route('/tickets', methods=['GET'])
def get_tickets():
    """ Get all tickets """
    try:
        tickets = list(get_ticket_collection().find())
        serialized_tickets = [Ticket.serialize_ticket(ticket) for ticket in tickets]
        return jsonify(serialized_tickets), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch tickets: {str(e)}"}), 500
    
@ticket_bp.route('/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """ Get a ticket by ID """
    try:
        ticket = get_ticket_collection().find_one({"_id": ObjectId(ticket_id)})
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
  
        serialized_ticket = Ticket.serialize_ticket(ticket)
        return jsonify(serialized_ticket), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch ticket: {str(e)}"}), 500

@ticket_bp.route('/tickets/<ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """ Update a ticket's status, owner, is_transferable, or pending_transfer_to """
    data = request.json
    print(f"Updating ticket {ticket_id} with data:", data)
    update_data = {}

    if "status" in data:
        update_data["status"] = data["status"]
    
    if "is_transferable" in data:
        update_data["is_transferable"] = bool(data["is_transferable"])
    
    if "owner_id" in data:
        update_data["owner_id"] = str(data["owner_id"])
    
    # Add support for pending_transfer_to
    if "pending_transfer_to" in data:
        if data["pending_transfer_to"] is None:
            result = get_ticket_collection().update_one(
                {"_id": ObjectId(ticket_id)},
                {
                    "$unset": {"pending_transfer_to": ""},
                    "$set": {k: v for k, v in update_data.items() if k != "pending_transfer_to"}
                }
            )
        else:
            update_data["pending_transfer_to"] = data["pending_transfer_to"]
    
    if not update_data and "pending_transfer_to" not in data:
        return jsonify({"error": "No valid fields to update"}), 400

    update_data["updated_at"] = datetime.utcnow()
    
    if update_data:
        result = get_ticket_collection().update_one(
            {"_id": ObjectId(ticket_id)}, 
            {"$set": update_data}
        )
        print(f"Update result: matched={result.matched_count}, modified={result.modified_count}")

    if result.matched_count == 0:
        return jsonify({"error": "Ticket not found"}), 404

    return jsonify({"message": "Ticket updated"}), 200

@ticket_bp.route('/tickets/<ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """ Delete a ticket """
    result = get_ticket_collection().delete_one({"_id": ObjectId(ticket_id)})
    
    if result.deleted_count == 0:
        return jsonify({"error": "Ticket not found"}), 404

    return jsonify({"message": "Ticket deleted"}), 200

@ticket_bp.route('/tickets/check_transfer_eligibility', methods=['POST'])
def check_ticket_transfer_eligibility():
    """Check if one or more tickets are eligible for transfer"""
    data = request.json
    required_fields = ["ticket_ids"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        ticket_ids = [ObjectId(ticket_id) for ticket_id in data["ticket_ids"]]

        tickets = list(get_ticket_collection().find({"_id": {"$in": ticket_ids}}))

        if not tickets:
            return jsonify({"error": "No matching tickets found"}), 404

        # Process tickets and check eligibility using serialization
        eligibility_results = []
        for ticket in tickets:
            serialized_ticket = Ticket.serialize_ticket(ticket)
            eligibility_results.append({
                "ticket_id": serialized_ticket["_id"],
                "is_transferable": serialized_ticket["is_transferable"],
            })

        return jsonify({"eligibility": eligibility_results}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@ticket_bp.route('/tickets/<string:ticket_id>/update_qr', methods=['PUT'])
def update_ticket_qr(ticket_id):
    data = request.json
    qr_code = data.get("qr_code")

    if not qr_code:
        return jsonify({"error": "Missing qr_code"}), 400

    result = get_ticket_collection().update_one(
        {"_id": ObjectId(ticket_id)},
        {"$set": {"qr_code": qr_code, "updated_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Ticket not found"}), 404

    return jsonify({"message": "QR code updated successfully"}), 200

@ticket_bp.route('/tickets/pending/<recipient_email>', methods=['GET'])
def get_pending_transfers(recipient_email):
    """Get all tickets pending transfer to a specific email"""
    try:
        tickets = list(get_ticket_collection().find({
            "status": "PENDING_TRANSFER",
            "pending_transfer_to": recipient_email
        }))

        print(f"Found {len(tickets)} pending transfers for {recipient_email}")
        
        serialized_tickets = [Ticket.serialize_ticket(ticket) for ticket in tickets]
        return jsonify(serialized_tickets), 200
    except Exception as e:
        print(f"Error in get_pending_transfers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ticket_bp.route('/tickets/category/<int:cat_id>', methods=['GET'])
def get_tickets_by_category(cat_id):
    try:
        query = {"cat_id": cat_id}
        owner_id = request.args.get("owner_id")
        event_id = request.args.get("event_id")
        event_date_id = request.args.get("event_date_id")
        status = request.args.get("status")
        
        if owner_id:
            query["owner_id"] = owner_id
        if event_id:
            try:
                query["event_id"] = int(event_id)
            except ValueError:
                query["event_id"] = event_id
        if event_date_id:
            try:
                query["event_date_id"] = int(event_date_id)
            except ValueError:
                query["event_date_id"] = event_date_id
        if status:
            query["status"] = status

        tickets = list(get_ticket_collection().find(query))
        
        if not tickets:
            return jsonify({"message": f"No tickets found for category ID {cat_id}"}), 200
            
        serialized_tickets = [Ticket.serialize_ticket(ticket) for ticket in tickets]
        return jsonify(serialized_tickets), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch tickets by category: {str(e)}"}), 500

# Register the blueprint
app.register_blueprint(ticket_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)