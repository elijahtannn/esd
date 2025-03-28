# test_notification.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Add parent directory to path

from services import send_transfer_notification
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rabbitmq_notification():
    """Test the RabbitMQ notification functionality"""
    test_email = "test@example.com"
    test_message = "This is a test notification message"
    test_event_type = "refund.test.notification"
    
    logger.info("Attempting to send test notification...")
    result = send_transfer_notification(
        user_email=test_email,
        message=test_message,
        event_type=test_event_type
    )
    
    if result:
        logger.info("✅ Notification sent successfully!")
    else:
        logger.error("❌ Failed to send notification")
        
    return result

if __name__ == "__main__":
    test_rabbitmq_notification()