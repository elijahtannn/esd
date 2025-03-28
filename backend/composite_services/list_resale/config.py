import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://127.0.0.1:5001")
    OUTSYSTEMS_EVENT_API_URL = os.getenv("OUTSYSTEMS_EVENT_API_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5003")