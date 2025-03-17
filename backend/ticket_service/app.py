from flask import Flask
from config import Config
from models import init_db
from routes import ticket_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db(app)

# Register Blueprint
app.register_blueprint(ticket_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)