import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Service URLs
    TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://127.0.0.1:5001")
    ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8003")
    PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://127.0.0.1:8002")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5003")
    
    # RabbitMQ Configuration
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "host.docker.internal")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
    
    # Exchange and routing configuration
    EXCHANGE_NAME = "refund.exchange"
    ROUTING_KEY = "refund.user.complete"