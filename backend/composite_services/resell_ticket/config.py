import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Service URLs
    TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://localhost:5001")
    OUTSYSTEMS_EVENT_API_URL = os.getenv("OUTSYSTEMS_EVENT_API_URL", "https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5003")
    
    # RabbitMQ Configuration - Important! Use localhost for local testing
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
    EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "ticketing.exchange")
    EXCHANGE_TYPE = os.getenv("EXCHANGE_TYPE", "topic")