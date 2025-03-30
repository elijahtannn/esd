import requests
from config import Config

def get_ticket_details(ticket_id):
    """Fetch ticket details from Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"

    response = requests.get(url)

    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from Ticket Service"}

    return response_data, response.status_code

def update_ticket_status(ticket_id):
    """Update ticket status to 'RESALE' in Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"
    payload = {"status": "RESALE"}
    
    response = requests.put(url, json=payload)
    return response.json(), response.status_code

def update_event_inventory(cat_id, resale_count):
    """Update event inventory in OutSystems Event Service"""
    url = f"{Config.OUTSYSTEMS_EVENT_API_URL}/events/dates/categories/{cat_id}/inventory/resale"
    
    headers = {
        "Content-Type": "application/json",
    }

    payload = {"Count": resale_count}

    response = requests.put(url, json=payload, headers=headers)
    
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from OutSystems"}

    return response_data, response.status_code
