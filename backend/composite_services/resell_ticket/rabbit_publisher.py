import pika
import json
import os
from config import Config

class RabbitMQPublisher:
    """Service to publish messages to RabbitMQ"""

    def __init__(self):
        # Get values from environment or config
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
        self.exchange_name = os.getenv("EXCHANGE_NAME", "ticketing.exchange")
        self.exchange_type = os.getenv("EXCHANGE_TYPE", "topic")

        # Print the actual URL for debugging
        print(f"Initialized RabbitMQ publisher with URL: {self.rabbitmq_url}")
    
    def _create_connection(self):
        """Create a connection to RabbitMQ"""
        # Parse URL for connection parameters
        if self.rabbitmq_url.startswith('amqp://'):
            # Strip 'amqp://' from the URL
            credentials_url = self.rabbitmq_url[7:]
            
            # Split credentials and host
            if '@' in credentials_url:
                credentials, host_port = credentials_url.split('@')
                username, password = credentials.split(':')
            else:
                host_port = credentials_url
                username, password = 'guest', 'guest'
            
            # Split host and port
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host, port = host_port, 5672
            
            # Create connection parameters
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=pika.PlainCredentials(username, password)
            )
            return pika.BlockingConnection(parameters)
        else:
            return pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
    
    def publish_resale_availability(self, event_id, event_name, ticket_details=None):
        """
        Publish a message to notify about resale ticket availability
        """
        try:
            print(f"Attempting to publish notification for event {event_id}")
            print(f"Connecting to RabbitMQ at {self.rabbitmq_url}")
            
            # Create connection and channel
            connection = self._create_connection()
            print("RabbitMQ connection established")
            
            channel = connection.channel()
            print("RabbitMQ channel created")
            
            # Declare exchange
            channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type=self.exchange_type,
                durable=True
            )
            print(f"Exchange '{self.exchange_name}' declared")
            
            # Prepare message payload
            message = {
                "eventType": "ticket.resale.available",
                "eventId": str(event_id),
                "eventName": event_name
            }

            if ticket_details and isinstance(ticket_details, dict):
                for key, value in ticket_details.items():
                    message[key] = value

            message_body = json.dumps(message)
            print(f"📤 Publishing message: {message_body[:100]}...")
            
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key="ticket.resale.available",
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            print("Message published successfully")
            
            # Close connection
            connection.close()
            print("RabbitMQ connection closed")
            return True
                
        except Exception as e:
            print(f"Error publishing resale availability message: {str(e)}")
            import traceback
            traceback.print_exc()
            return False