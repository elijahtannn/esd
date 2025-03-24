from flask_pymongo import PyMongo
from datetime import datetime
from bson.objectid import ObjectId

mongo = PyMongo()

def init_db(app):
    """Initialize the MongoDB connection"""
    mongo.init_app(app)

def get_ticket_collection():
    """Get the ticket collection from MongoDB"""
    return mongo.db.tickets

class Ticket:
    """Ticket Model"""

    def __init__(self, event_date_id, cat_id, owner_id, seat_info, status="available", is_transferable=True, qr_code=None):
        self.event_date_id = int(event_date_id)  # Stored as integer
        self.cat_id = int(cat_id)  # Stored as integer
        self.owner_id = ObjectId(owner_id)  # MongoDB ObjectId for user reference
        self.seat_info = seat_info
        self.status = status
        self.is_transferable = is_transferable
        self.qr_code = qr_code if qr_code else ""
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert Ticket object to a dictionary for MongoDB storage"""
        return {
            "event_date_id": self.event_date_id,
            "cat_id": self.cat_id,
            "owner_id": str(self.owner_id),  # Convert ObjectId to string
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
        if "_id" in ticket_dict:
            ticket_dict["_id"] = str(ticket_dict["_id"])
        if "owner_id" in ticket_dict:
            ticket_dict["owner_id"] = str(ticket_dict["owner_id"])
        if "created_at" in ticket_dict:
            ticket_dict["created_at"] = ticket_dict["created_at"].isoformat()
        if "updated_at" in ticket_dict:
            ticket_dict["updated_at"] = ticket_dict["updated_at"].isoformat()
        return ticket_dict
