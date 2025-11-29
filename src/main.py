import threading
import logging
import os
import json
from flask import Flask, send_from_directory, request, jsonify
from dotenv import load_dotenv
from utils import scraper
from utils import users

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)

# Initialize Flask App
# static_folder='www' tells Flask to look for files in src/www
app = Flask(__name__, static_folder='www')

# --- API Endpoints ---

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    Endpoint to initiate login.
    Expects JSON: { "email": "user@example.com" }
    """
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400

    if users.login(email):
        return jsonify({"success": True, "message": "OTP sent successfully"}), 200
    else:
        return jsonify({"success": False, "error": "Failed to send OTP"}), 500

@app.route('/api/verify', methods=['POST'])
def api_verify():
    """
    Endpoint to verify OTP.
    Expects JSON: { "email": "user@example.com", "otp": "123456" }
    """
    data = request.json
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"success": False, "error": "Email and OTP are required"}), 400

    token = users.verify_otp(email, otp)
    
    if token:
        return jsonify({"success": True, "token": token}), 200
    else:
        return jsonify({"success": False, "error": "Invalid OTP"}), 401

@app.route('/api/articles', methods=['GET'])
def api_articles():
    """
    Returns the scraped articles from the JSON file.
    """
    file_path = "hacker_news_articles.json"
    if not os.path.exists(file_path):
        return jsonify([]), 200
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        logging.error(f"Error reading articles: {e}")
        return jsonify({"error": "Failed to fetch articles"}), 500

# --- Static File Serving ---

@app.route('/')
def serve_index():
    """Serves the index.html file."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serves any other file from the www directory (css, js, images)."""
    return send_from_directory(app.static_folder, path)

# --- Main Entry Point ---

if __name__ == "__main__":
    logging.info("Starting SheepAI Backend...")

    # 1. Start the Scraper in a background thread
    # daemon=True ensures the thread closes when the server stops
    scraper_thread = threading.Thread(target=scraper.monitor_feed, daemon=True)
    scraper_thread.start()

    # 2. Start the Flask Web Server
    # host='0.0.0.0' makes it accessible on your local network
    # port=8080 is the port (http://localhost:8080)
    logging.info("Server running at http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)