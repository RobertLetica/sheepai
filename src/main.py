import threading
import logging
import os
import json
from flask import Flask, send_from_directory, request, jsonify, redirect
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

    # Get the server's root URL (e.g., http://localhost:8080) to create the link
    base_url = request.url_root.rstrip('/')

    # Pass base_url to users.login so it can generate the correct link
    if users.login(email, base_url):
        return jsonify({"success": True, "message": "OTP sent successfully"}), 200
    else:
        return jsonify({"success": False, "error": "Failed to send OTP"}), 500

@app.route('/api/verify', methods=['POST'])
def api_verify():
    """
    Endpoint to verify OTP (Manual Entry via API).
    Expects JSON: { "email": "...", "otp": "..." }
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

@app.route('/api/verify_link', methods=['GET'])
def api_verify_link():
    """
    Endpoint for Email Click Verification.
    URL: /api/verify_link?email=...&code=...
    Redirects to home page with token on success.
    """
    email = request.args.get('email')
    otp = request.args.get('code')

    if not email or not otp:
        return "Invalid Verification Link", 400

    # Verify the OTP using the same logic as the manual endpoint
    token = users.verify_otp(email, otp)
    
    if token:
        # Redirect to the main page with the token in the URL parameters
        # Your frontend JS should look for these params to log the user in
        return redirect(f'/?token={token}&email={email}')
    else:
        return "<h3>Verification Failed</h3><p>Invalid or expired link.</p>", 401

@app.route('/api/extract_tags', methods=['POST'])
def api_extract_tags():
    """
    Endpoint to extract tags from text without auth (for landing page).
    Expects JSON: { "text": "..." }
    """
    data = request.json
    text = data.get('text')

    if not text:
        return jsonify({"success": False, "error": "Text is required"}), 400

    from utils import ai
    try:
        tags = ai.extract_tags_from_user_description(text)
        return jsonify({"success": True, "tags": tags}), 200
    except Exception as e:
        logging.error(f"Extraction failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/articles', methods=['GET'])
def api_articles():
    """
    Returns the scraped articles from the JSON file.
    Requires Authorization header with Bearer token.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized: Missing or invalid token"}), 401

    token = auth_header.split(' ')[1]
    user = users.validate_token(token)

    if not user:
        return jsonify({"error": "Unauthorized: Invalid token"}), 401

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

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Endpoint for article chatbot.
    Expects JSON: { "query": "...", "article_title": "...", "article_content": "..." }
    Requires Authentication.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header.split(' ')[1]
    user = users.validate_token(token)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    query = data.get('query')
    article_title = data.get('article_title')
    article_content = data.get('article_content')

    if not query or not article_content:
        return jsonify({"error": "Query and content are required"}), 400

    from utils import ai
    response = ai.chat_with_article(query, article_title, article_content)

    return jsonify({"response": response}), 200

@app.route('/api/user/profile', methods=['GET', 'POST'])
def api_user_profile():
    """
    GET: Retrieve user profile.
    POST: Update user profile (tags, interests_prompt).
    Requires Authentication.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header.split(' ')[1]
    user = users.validate_token(token)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'GET':
        return jsonify({
            "email": user.get('email'),
            "tags": user.get('tags', []),
            "interests_prompt": user.get('interests_prompt', "")
        }), 200

    if request.method == 'POST':
        data = request.json
        explicit_tags = data.get('tags', [])
        # We still accept interests_prompt to save it, but we don't necessarily extract from it
        # unless specifically requested or if it's a new prompt.
        # However, per user request to "remove the tag extractor from the settings page"
        # and "only list user entered tags", we should probably rely on the frontend
        # sending the final list of tags (which might include previously extracted ones).

        # If the frontend sends tags, we should trust them as the current state.
        # The user said "do the extraction in the first prompt... and then fix the settings page... removing the tag extractor from the settings page".
        # This implies the settings page will just send the list of tags.

        interests_prompt = data.get('interests_prompt', "")

        # We will NOT do AI extraction here anymore, assuming the frontend handles it
        # (e.g. on landing page) or the user manually manages tags.
        # If we need to support extraction, we should use the dedicated /api/extract_tags endpoint
        # or a specific flag, but for now, we follow the "remove tag extractor" instruction.

        updated_user = users.update_user_profile(token, explicit_tags, interests_prompt)

        if updated_user:
            return jsonify({"success": True, "user": updated_user}), 200
        else:
            return jsonify({"error": "Failed to update profile"}), 500

# --- Static File Serving ---

@app.route('/verify.html')
def serve_verify_page():
    """
    Special handler for verify.html.
    """
    return send_from_directory(app.static_folder, 'verify.html')

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
