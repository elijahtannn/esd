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

def get_event_details(event_id):
    """Fetch event details from Event Service"""
    url = f"{Config.OUTSYSTEMS_EVENT_API_URL}/events/{event_id}"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from Event Service"}
        
    return response_data, response.status_code

def get_category_details(cat_id):
    """Fetch ticket category details from Event Service"""
    url = f"{Config.OUTSYSTEMS_EVENT_API_URL}/events/dates/categories/{cat_id}"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from Event Service"}
        
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

def get_interested_users(event_id):
    """Fetch users interested in an event from User Service"""
    url = f"{Config.USER_SERVICE_URL}/events/{event_id}/interested-users"
    
    response = requests.get(url)
    
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Invalid JSON response from User Service"}
        
    return response_data.get("users", []), response.status_code