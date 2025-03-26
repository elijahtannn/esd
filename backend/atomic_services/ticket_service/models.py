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

    def __init__(self, event_id, event_date_id, cat_id, owner_id, seat_info, status="available", is_transferable=True, qr_code=None):
        self.event_id = int(event_id)
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
            "event_id": self.event_id,
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
        serialized = ticket_dict.copy()  # Create a copy to avoid modifying the original
        
        if "_id" in serialized:
            serialized["_id"] = str(serialized["_id"])
        if "owner_id" in serialized:
            serialized["owner_id"] = str(serialized["owner_id"])
        if "created_at" in serialized:
            serialized["created_at"] = serialized["created_at"].isoformat() if serialized["created_at"] else None
        if "updated_at" in serialized:
            serialized["updated_at"] = serialized["updated_at"].isoformat() if serialized["updated_at"] else None
        
        return serialized
