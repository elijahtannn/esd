from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
import json
import logging
import random
import string
import time

app = Flask(__name__)
CORS(app)

load_dotenv()
# Service URLs
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://127.0.0.1:5001")
EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5003")
REFUND_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5004")


def getAllCatTickets(cat_id):
    response = requests.get(f"{TICKET_SERVICE_URL}/tickets/category/{cat_id}")
    responseData = json.loads(response.content.decode("utf-8-sig"))
    
    if isinstance(responseData, list):
        # It's an array of tickets
        print("Received an array of tickets")
        return responseData
    elif isinstance(responseData, dict) and 'message' in responseData:
        # It's a dictionary with a 'message' key
        print(f"Message received: {responseData['message']}")
        return []
    else:
        # Unexpected response format
        print("Unexpected response format")
        return None


# Create new ticket
def createTicket(user_id, event_date_id, cat_id, quantity, event_id, event_category, all_cat_tickets):
    ticketIds = []
    used_resale_tickets = []
    assigned_seats = set()

    # Get all seat infos
    all_seat_infos = []
    for ticket in all_cat_tickets:
        all_seat_infos.append(ticket['seat_info'])

    # Get all existing resale tickets (if any)
    resale_tickets = []
    sorted_ticketed = sorted(all_cat_tickets, key=lambda x: datetime.fromisoformat(x["created_at"]))
    for ticket in sorted_ticketed:
        if ticket['status'] == 'RESALE':
            resale_tickets.append(ticket)

    for num in range(quantity):

        # If there are no resale tickets listed
        if not resale_tickets:
            # Only concerts has seat info
            if event_category == 'Concert':
                
                seat_info = ""

                # Check if seat info is still empty or if it already exist
                while seat_info == "" or seat_info in all_seat_infos:
                    # Generate seat info
                    seat_info = generate_unique_seat(assigned_seats)

            else:
                seat_info = "Not Applicable"
            
            reserve_data = {
                "event_date_id": event_date_id,
                "cat_id": cat_id,
                "owner_id": user_id,
                "seat_info": seat_info,
                "num_tickets": 1,
                "is_transferable": True,
                "status": "RESERVED",
                "event_id": event_id,
            }
            reserve_resp = requests.post(f"{TICKET_SERVICE_URL}/tickets/reserve", json=reserve_data)
            reserve_result = reserve_resp.json()
            ticketId = reserve_result['ticket_ids'][0]
            ticketIds.append(ticketId)
            print("There is NO existing resale: ", ticketId)

            # generate QR code and update db
            qr_url = generate_qr_code_url(ticketId)
            requests.put(f"{TICKET_SERVICE_URL}/tickets/{ticketId}/update_qr", json={"qr_code": qr_url})    

        else:
            # If there are resale tickets listed 
            # update owner id and status
            ticketId = resale_tickets[0]['_id']
            print("There is existing resale: ", ticketId)

            used_resale_tickets.append(resale_tickets[0])
            ticketIds.append(ticketId)
            updateTicket(ticketId, user_id, "RESERVED")
            
            resale_tickets.pop(0)

    return ticketIds, used_resale_tickets

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
def checkTicketStatus(all_reserved_ticket_ids, all_used_resale_tickets):

    purchaseStatus = False
    for ticketId in all_reserved_ticket_ids:
        print("current ticket", ticketId)
        try:
            # ticket_id_object = ObjectId(ticketId)
            response = requests.get(f"{TICKET_SERVICE_URL}/tickets/{ticketId}")
            responseData = json.loads(response.content.decode("utf-8-sig"))

            ticketStatus = responseData['status']
            print("Status:", ticketStatus)

            if ticketStatus != 'SOLD':
                # it its a resale ticket, dont delete but revert owner id and status
                print("ALL RESALE:",all_used_resale_tickets)
                for ticket in all_used_resale_tickets:
                    if ticket["_id"] == ticketId:
                        print("FOUND IN RESALE:",ticket)    
                        updateTicket(ticketId, ticket["owner_id"], "RESALE")
                        break
                else:
                    # Delete ticket if user did not buy the ticket within the time. Leave it untouched if user bought the ticket
                    print("delete:", ticketId)
                    response = requests.delete(f"{TICKET_SERVICE_URL}/tickets/{ticketId}")
            else:
                # If one ticket has the sold status, all ticket will have the same status as it is in the same order
                purchaseStatus = True

                # refund all the resale ticket if any
                for ticket in all_used_resale_tickets:
                    refund_data = {
                        "ticket_id": ticket['_id'],
                        "owner_id": ticket['owner_id'],
                    }
                    response = requests.post(f"{REFUND_SERVICE_URL}/refund", json=refund_data)

        except Exception as e:
            print("Error:", str(e))
            return False
    
    return purchaseStatus

# Updating ticket owner id and status
def updateTicket(ticketId, owner_id, status):
    updated_data = {
        "owner_id": owner_id,
        "status": status,
    }
    response = requests.put(f"{TICKET_SERVICE_URL}/tickets/{ticketId}", json=updated_data)
    print(response)
    return True

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
        event_category = data["eventCategory"]
        
        all_reserved_ticket_ids = []
        all_used_resale_tickets = []
        total_quantity = 0

        # Create tickets
        for item in selected_tickets:
            cat_id = item["catId"]
            quantity = item["quantity"]
            all_cat_tickets = getAllCatTickets(cat_id)

            total_quantity += quantity

            if not all([cat_id, quantity]):
                continue

            # create new ticket entry
            createdTickets, used_resale_tickets = createTicket(user_id, event_date_id, cat_id, quantity, event_id, event_category, all_cat_tickets) #store all ticket Ids for this Cat
            all_used_resale_tickets = used_resale_tickets
            all_reserved_ticket_ids.extend(createdTickets)

            # Update event cat available tickets
            decrease_cat_available_tickets(cat_id, quantity)

        # Update event total available tickets
        decrease_event_available_tickets(event_date_id, total_quantity)

        print("all:" , all_reserved_ticket_ids)
        print("resale: ", all_used_resale_tickets)
        print("Reserved ticket while waiting for user to complete order purchase")

        # Wait for 3 minutes for user to complete order purchase
        time.sleep(30) #will update this to 3 minutes: 180

        purchaseStatus = checkTicketStatus(all_reserved_ticket_ids, all_used_resale_tickets)
        # purchaseStatus = True #for testing

        print(purchaseStatus)
                
        if purchaseStatus:
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
