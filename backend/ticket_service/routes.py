from flask import Blueprint, request, jsonify
from models import get_ticket_collection, Ticket
from bson.objectid import ObjectId
from datetime import datetime

ticket_bp = Blueprint('ticket_bp', __name__)

@ticket_bp.route('/tickets/reserve', methods=['POST'])
def create_tickets():
    """ Create one or more tickets in a single request """
    data = request.json
    required_fields = ["event_date_id", "cat_id", "owner_id", "seat_info"]
    
    # Ensure all required fields are present
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Default to 1 if num_tickets is not provided
        num_tickets = int(data.get("num_tickets", 1))  
        if num_tickets <= 0:
            return jsonify({"error": "Number of tickets must be at least 1"}), 400

        tickets = []
        for _ in range(num_tickets):
            new_ticket = Ticket(
                event_date_id=int(data["event_date_id"]),  # Ensure integer
                cat_id=int(data["cat_id"]),  # Ensure integer
                owner_id=data["owner_id"],  # MongoDB ObjectId for user
                seat_info=data["seat_info"],  # Same seat info for all (can be modified later)
                status="reserved",  # Initial status
                is_transferable=data.get("is_transferable", True),
                qr_code=data.get("qr_code", "")
            )
            tickets.append(new_ticket.to_dict())

        # Insert all tickets in one operation for efficiency
        result = get_ticket_collection().insert_many(tickets)

        return jsonify({
            "message": f"{num_tickets} ticket(s) reserved successfully",
            "ticket_ids": [str(ticket_id) for ticket_id in result.inserted_ids]
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
    tickets = list(get_ticket_collection().find())
    for ticket in tickets:
        ticket["_id"] = str(ticket["_id"])  # Convert ObjectId to string
    return jsonify(tickets), 200

@ticket_bp.route('/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """ Get a ticket by ID """
    ticket = get_ticket_collection().find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    ticket["_id"] = str(ticket["_id"])
    return jsonify(ticket), 200

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

        # Process tickets and check eligibility
        eligibility_results = []
        for ticket in tickets:
            eligibility_results.append({
                "ticket_id": str(ticket["_id"]),
                "is_transferable": ticket["is_transferable"],
            })

        return jsonify({"eligibility": eligibility_results}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400