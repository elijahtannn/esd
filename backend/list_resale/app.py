from flask import Flask
from config import Config
from routes import resale_bp

app = Flask(__name__)
app.config.from_object(Config)

# Register Blueprint
app.register_blueprint(resale_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)