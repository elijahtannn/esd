import requests
from config import Config

def get_ticket_details(ticket_id):
    """Fetch ticket details from Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"

    response = requests.get(url)
    print(f"Raw response: {response.text}") 
    try:
        response_data = response.json()
        if response.status_code == 200:
            if response_data.get('status') == 'sold':
                return response_data, 200
            else:
                return {"error": "Ticket is not sold"}, 400
        else:
            return {"error": "Failed to fetch ticket details"}, response.status_code
    except ValueError:
        return {"error": "Invalid JSON response from Ticket Service"}, 500


def update_order_refund_status(order_id, seller_id, ticket_id):
    """Update order status to 'RESALE' and add refund details in Order Service"""
    url = f"{Config.ORDER_SERVICE_URL}/orders/user/{order_id}"
    payload = {
        "status": "RESALE",
        "refundDetails": {
            "sellerId": seller_id,
            "ticketId": ticket_id
        }
    }
    
    response = requests.put(url, json=payload)
    return response.json(), response.status_code


def refund_payment_to_seller(order_id, seller_id, amount):
    """Refund payment to seller and update order status"""
    url = f"{Config.ORDER_SERVICE_URL}/orders/user/{order_id}/refund"
    payload = {
        "sellerId": seller_id,
        "amount": amount,
        "status": "REFUNDED"
    }
    
    response = requests.post(url, json=payload)
    return response.json(), response.status_code

def update_ticket_status(ticket_id, new_status):
    """Update ticket status in Ticket Service"""
    url = f"{Config.TICKET_SERVICE_URL}/tickets/{ticket_id}"
    payload = {"status": new_status}
    
    response = requests.put(url, json=payload)
    return response.json(), response.status_code

def refund_payment(seller_id, amount):
    """Refund payment to seller"""
    url = f"{Config.PAYMENT_SERVICE_URL}/refund"
    payload = {
        "sellerId": seller_id,
        "amount": amount
    }
    response = requests.post(url, json=payload)
    return response.json(), response.status_code