import pika
import os
import time

# Get the RabbitMQ URL from environment variable
rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672')
print(f'Using RabbitMQ URL: {rabbitmq_url}')

# Try to connect to RabbitMQ
max_attempts = 5
for attempt in range(max_attempts):
    try:
        print(f'Attempt {attempt+1}/{max_attempts} to connect to RabbitMQ...')
        
        # Parse URL for connection parameters
        if rabbitmq_url.startswith('amqp://'):
            # Strip 'amqp://' from the URL
            credentials_url = rabbitmq_url[7:]
            
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
            
            print(f'Connecting to {host}:{port} with user {username}')
            
            # Create connection parameters
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=pika.PlainCredentials(username, password)
            )
            connection = pika.BlockingConnection(parameters)
        else:
            # If the URL doesn't start with 'amqp://', try to use it directly
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        
        channel = connection.channel()
        print('Successfully connected to RabbitMQ!')
        
        # Declare exchange
        exchange_name = 'ticketing.exchange'
        exchange_type = 'topic'
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=True
        )
        print(f'Successfully declared exchange: {exchange_name}')
        
        # Publish a test message
        message = '{"eventType": "test.message", "content": "Hello from test script"}'
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='test.message',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        print('Successfully published test message!')
        
        # Close connection
        connection.close()
        print('Connection closed successfully')
        
        break  # Exit the loop if successful
    except Exception as e:
        print(f'Connection failed: {e}')
        if attempt < max_attempts - 1:
            print('Retrying in 2 seconds...')
            time.sleep(2)
        else:
            print('All connection attempts failed.')