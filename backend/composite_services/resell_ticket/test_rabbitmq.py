# test_publisher.py
from rabbit_publisher import RabbitMQPublisher
import os

# Force the URL to use localhost
os.environ["RABBITMQ_URL"] = "amqp://guest:guest@localhost:5672"

# Create the publisher with verbose logging
publisher = RabbitMQPublisher()

# Print the actual URL being used
print(f"Using RabbitMQ URL: {publisher.rabbitmq_url}")

# Test publish a message
result = publisher.publish_resale_availability(
    event_id="12",
    event_name="Test Event",
    ticket_details={
        "ticketPrice": 75.00,
        "ticketQuantity": 1,
        "eventDate": "2025-06-15",
        "eventLocation": "Test Venue"
    }
)

# Print the result
print(f"Publish result: {'Success' if result else 'Failed'}")