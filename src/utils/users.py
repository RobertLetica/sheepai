import json
import os
import random
import uuid
import logging
from datetime import datetime
from utils import mail

USERS_FILE = "users.json"

def load_users():
    """Load users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_users(users):
    """Save users to the JSON file."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def login(email: str):
    """
    Initiates the login process:
    1. Generates a 6-digit OTP.
    2. Creates the user if they don't exist.
    3. Saves the OTP.
    4. Sends the email.
    """
    users = load_users()
    otp = str(random.randint(100000, 999999))
    
    user_found = False
    for user in users:
        if user['email'] == email:
            user['otp'] = otp
            user_found = True
            break
    
    if not user_found:
        new_user = {
            "email": email,
            "otp": otp,
            "token": None,
            "tags": [],
            "interests_prompt": "",
            "last_online": ""
        }
        users.append(new_user)
    
    save_users(users)
    
    # Send email
    try:
        mail.send_otp_email(to_email=email, code=otp)
        logging.info(f"OTP sent to {email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send OTP to {email}: {e}")
        return False

def verify_otp(email: str, code: str):
    """
    Verifies the OTP provided by the user.
    If valid, generates and returns an access token.
    """
    users = load_users()
    
    for user in users:
        if user['email'] == email:
            if user['otp'] == code:
                # Generate Token
                token = str(uuid.uuid4())
                user['token'] = token
                user['otp'] = None # Clear OTP after use
                user['last_online'] = datetime.now().isoformat()
                
                save_users(users)
                logging.info(f"User {email} logged in successfully.")
                return token
            else:
                logging.warning(f"Invalid OTP attempt for {email}")
                return None
                
    logging.warning(f"User {email} not found during verification.")
    return None