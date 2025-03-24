from flask import Blueprint, request, jsonify
from models import get_ticket_collection, Ticket
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import threading


ticket_bp = Blueprint('ticket_bp', __name__)

# Helper: Release reserved ticket and delete if unconfirmed

def release_ticket_after_delay(ticket_ids, delay_seconds=180):
    def release():
        ticket_collection = get_ticket_collection()
        now = datetime.utcnow()
        expired_time = now - timedelta(seconds=delay_seconds)
        result = ticket_collection.delete_many({
            "_id": {"$in": [ObjectId(tid) for tid in ticket_ids]},
            "status": "reserved",
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
            "owner_id": str(owner_id),  # Store owner_id as string
            "status": "reserved"
        })

        return jsonify({
            "message": f"Released and deleted {result.deleted_count} reserved ticket(s)",
            "ticket_ids": ticket_ids
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to release tickets: {str(e)}"}), 400

# Trigger the timer automatically in your reserve route
@ticket_bp.route('/tickets/reserve', methods=['POST'])
def create_tickets():
    data = request.json
    required_fields = ["event_date_id", "cat_id", "owner_id", "seat_info"]
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
                event_date_id=int(data["event_date_id"]),
                cat_id=int(data["cat_id"]),
                owner_id=data["owner_id"],
                seat_info=data["seat_info"],
                status="reserved",
                is_transferable=data.get("is_transferable", True),
                qr_code=data.get("qr_code", "")
            ).to_dict()
            ticket_dict["created_at"] = now
            ticket_dict["updated_at"] = now
            tickets.append(ticket_dict)

        result = get_ticket_collection().insert_many(tickets)
        inserted_ids = [str(ticket_id) for ticket_id in result.inserted_ids]

        # Set timer to release if not confirmed in 3 minutes
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
        ticket_ids = [ObjectId(ticket_id) for ticket_id in data["ticket_ids"]]

        # Find all matching tickets
        tickets = list(get_ticket_collection().find({"_id": {"$in": ticket_ids}}))
        
        if not tickets:
            return jsonify({"error": "No matching tickets found"}), 404

        # Check if any ticket is NOT in 'reserved' status
        for ticket in tickets:
            if ticket["status"] != "reserved":
                return jsonify({"error": f"Ticket {str(ticket['_id'])} is not reserved"}), 400

        # Update all tickets to 'sold'
        result = get_ticket_collection().update_many(
            {"_id": {"$in": ticket_ids}},
            {"$set": {"status": "sold", "updated_at": datetime.utcnow()}}
        )

        return jsonify({
            "message": f"Successfully updated {result.modified_count} ticket(s) to 'sold'"
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
            
        # Use the same serialization method as get_tickets()
        serialized_ticket = Ticket.serialize_ticket(ticket)
        return jsonify(serialized_ticket), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch ticket: {str(e)}"}), 500

@ticket_bp.route('/tickets/<ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """ Update a ticket's status or owner or is_transferable """
    data = request.json
    update_data = {}

    if "status" in data:
        update_data["status"] = data["status"]
    
    if "is_transferable" in data:
        update_data["is_transferable"] = bool(data["is_transferable"])
    
    if "owner_id" in data:
        update_data["owner_id"] = ObjectId(data["owner_id"])
    
    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    update_data["updated_at"] = datetime.utcnow()
    result = get_ticket_collection().update_one({"_id": ObjectId(ticket_id)}, {"$set": update_data})

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

        # Fetch the tickets from the database
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
