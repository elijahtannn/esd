from flask import Flask
from config import Config
from routes import resale_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}})

app.config.from_object(Config)
app.register_blueprint(resale_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)