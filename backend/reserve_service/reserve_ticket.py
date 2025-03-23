from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import pika
import json
import logging
import random
import string
import time
from bson.objectid import ObjectId


app = Flask(__name__)
CORS(app)

load_dotenv()
# Service URLs
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://127.0.0.1:5001")
EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://user-service:8000")

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "host.docker.internal")
EXCHANGE_NAME = "ticketing.exchange"
ROUTING_KEY = "ticket.purchase.success"


# Check if event category has sufficient ticket
def check_eventcat_inventory(event_date_id, ticket_quantity, catId):
    try:
        response = requests.get(f"{EVENT_SERVICE_URL}/events/dates/{event_date_id}/categories", timeout=10)
        if response.status_code != 200:
            return False, f"Failed to retrieve event data, status code: {response.status_code}", None, None

        event_data = json.loads(response.content.decode("utf-8-sig"))
        for cat in event_data['Cats']:
            if cat['Id'] == catId:  # Check and find cat id
                if cat['AvailableTickets'] > ticket_quantity:  # Check if AvailableTickets is greater than require ticket quantity
                    print(f"Category {cat['Cat']} (ID {cat['Id']}) has {cat['AvailableTickets']} tickets available.")
                    return True
                else:
                    print(f"Category {cat['Cat']} (ID {cat['Id']}) has no tickets available.")
                    return False

        return False, "event_data", None, None

    except Exception as e:
        return False, f"Error checking inventory: {str(e)}", None, None

# Create new ticket
def createTicket(user_id, event_date_id, cat_id, quantity):
    ticketIds = []
    assigned_seats = set()

    for num in range(quantity):

        # Generate seat info
        seat_info = generate_unique_seat(assigned_seats)
        
        reserve_data = {
            "event_date_id": event_date_id,
            "cat_id": cat_id,
            "owner_id": user_id,
            "seat_info": seat_info,
            "num_tickets": 1,
            "is_transferable": True,
            "status": "reserved",
        }
        reserve_resp = requests.post(f"{TICKET_SERVICE_URL}/tickets/reserve", json=reserve_data)
        reserve_result = reserve_resp.json()
        ticketId = reserve_result['ticket_ids'][0]
        ticketIds.append(ticketId)

        # generate QR code and update db
        qr_url = generate_qr_code_url(ticketId)
        requests.put(f"{TICKET_SERVICE_URL}/tickets/{ticketId}/update_qr", json={"qr_code": qr_url})    

    return ticketIds

# decrease event total available tickets
def decrease_event_available_tickets(event_date_id, total_quantity):
    try:
        response = requests.put(f"{EVENT_SERVICE_URL}/events/dates/{event_date_id}/inventory/purchase", json={"Count": total_quantity})
        return response.status_code == 200
    except Exception as e:
        print("Error updating available tickets:", str(e))
        return False
    
# decrease event cat available tickets 
def decrease_cat_available_tickets(cat_id, total_quantity):
    try:
        response = requests.put(f"{EVENT_SERVICE_URL}/events/dates/categories/{cat_id}/inventory/purchase", json={"Count": total_quantity})
        return response.status_code == 200
    except Exception as e:
        print("Error updating available tickets:", str(e))
        return False

# Generate QR code for seat
def generate_qr_code_url(ticket_id):
    base_url = "http://api.qrserver.com/v1/create-qr-code/"
    qr_content = f"ticket:{ticket_id}"
    qr_url = f"{base_url}?data={requests.utils.quote(qr_content)}&size=200x200"
    return qr_url

# Generate seat info 
def generate_unique_seat(existing_seats):
    while True:
        row = random.choice(string.ascii_uppercase)
        seat = random.randint(1, 50)
        seat_info = f"Row {row}, Seat {seat}"
        if seat_info not in existing_seats:
            existing_seats.add(seat_info)
            return seat_info
        

# After time frame, check ticket status to determine purchase status
def checkTicketStatus(all_reserved_ticket_ids):

    purchaseStatus = False
    for ticketId in all_reserved_ticket_ids:

        try:
            ticket_id_object = ObjectId(ticketId)
            response = requests.get(f"{TICKET_SERVICE_URL}/tickets/{ticket_id_object}")
            # print("hereeeeeeeeeee", response.text)
            responseData = json.loads(response.content.decode("utf-8-sig"))

            print("returnignngg" , responseData)
            ticketStatus = responseData['status']

            if ticketStatus != 'sold':
                # Delete ticket if user did not buy the ticket within the time. Leave it untouched if user bought the ticket
                response = requests.delete(f"{TICKET_SERVICE_URL}/tickets/{ticketId}")
                print(response.content)
            else:
                # If one ticket has the sold status, all ticket will have the same status as it is in the same order
                purchaseStatus = True
        except Exception as e:
            print("Error:", str(e))
            return False
    
    return purchaseStatus

# If user did not complete purchase within time frame: Revert back the event available ticket and cat available ticket
def revertTicketQuantity(event_date_id, selected_tickets):

    total_quantity = 0

    for ticket in selected_tickets:
        total_quantity+=ticket['quantity']

        try:
            response = requests.put(f"{EVENT_SERVICE_URL}/events/dates/categories/{ticket['catId']}/inventory/resale", json={"Count": ticket['quantity']})
        except Exception as e:
            print("Error updating available tickets:", str(e))
    try:
        response = requests.put(f"{EVENT_SERVICE_URL}/events/dates/{event_date_id}/inventory/resale", json={"Count": total_quantity})
    except Exception as e:
        print("Error updating available tickets:", str(e))   

    
    return True


logging.basicConfig(level=logging.INFO)

@app.route("/reserve_ticket", methods=["POST"])
def process_ticket_reserve():
    try:
        data = request.json
        user_id = data["userId"]
        selected_tickets = data["selectedTickets"]
        event_date_id = data["selectedDateId"]
        event_id = data["selectedEventId"]
        
        all_reserved_ticket_ids = []
        total_quantity = 0

        # Create tickets
        for item in selected_tickets:
            cat_id = item["catId"]
            quantity = item["quantity"]

            total_quantity += quantity

            if not all([cat_id, quantity]):
                continue

            isTicketAvailable = check_eventcat_inventory(event_date_id, quantity, cat_id)

            if not isTicketAvailable:
                return jsonify({"error": "no tickets available"}), 400
            else:
                # create new ticket entry
                createdTickets = createTicket(user_id, event_date_id, cat_id, quantity) #store all ticket Ids for this Cat
                all_reserved_ticket_ids.extend(createdTickets)

                # Update event cat available tickets
                decrease_cat_available_tickets(cat_id, quantity)

        # Update event total available tickets
        decrease_event_available_tickets(event_date_id, total_quantity)

        print("Reserved ticket while waiting for user to complete order purchase")

        # Wait for 3 minutes for user to complete order purchase
        time.sleep(5) #will update this to 3 minutes: 180

        purchaseStatus = checkTicketStatus(all_reserved_ticket_ids)

        if purchaseStatus == True:

            # Return successful output
            return jsonify({
                "status": True,
                "statement": "successfully reserved tickets",
                "user_id": user_id,
                "event_id": event_id,
                "event_date_id": event_date_id,
                "reserved_ticket_ids": all_reserved_ticket_ids,
                "tickets": selected_tickets,
            }), 200
        else:
            # increase back the available tickets for event and cats
            revertTicketQuantity(event_date_id, selected_tickets)

            return jsonify({
                "status": False,
                "statement": "User did not purchase the tickets within the time frame",
                "user_id": user_id,
                "event_id": event_id,
                "event_date_id": event_date_id,
                "reserved_ticket_ids": all_reserved_ticket_ids,
                "tickets": selected_tickets,
            }), 200

    except Exception as e:
        logging.exception("Unexpected error during ticket reserving processing")
        return jsonify({"error": "Service error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8006, debug=True)
