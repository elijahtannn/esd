from flask import Flask
from routes import refund_bp
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(refund_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)