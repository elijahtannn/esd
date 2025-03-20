import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:5001")
    OUTSYSTEMS_EVENT_API_URL = os.getenv("OUTSYSTEMS_EVENT_API_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")