import json
import os
import random
import uuid
import logging
from datetime import datetime
from utils import mail

# Path relative to where main.py runs
USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "users.json")

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def login(email: str):
    """
    1. Generates 6-digit OTP.
    2. Creates/Updates user.
    3. Sends OTP via Email.
    """
    users = load_users()
    otp = str(random.randint(100000, 999999))
    
    user_found = False
    for user in users:
        if user.get('email') == email:
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
    
    logging.info(f"Sending OTP to {email}...")
    success = mail.send_otp_email(to_email=email, code=otp)
    
    if success:
        logging.info(f"OTP successfully sent to {email}")
        return True
    else:
        logging.error(f"Failed to send OTP to {email}")
        return False

def verify_otp(email: str, code: str):
    """
    Verifies OTP and returns a new Access Token if valid.
    """
    users = load_users()
    
    for user in users:
        if user.get('email') == email:
            # Check if OTP matches and isn't empty
            if user.get('otp') and str(user['otp']) == str(code).strip():
                # Generate Token
                token = str(uuid.uuid4())
                user['token'] = token
                user['otp'] = None  # Clear OTP to prevent replay
                user['last_online'] = datetime.now().isoformat()
                
                save_users(users)
                logging.info(f"User {email} verified successfully.")
                return token
            else:
                logging.warning(f"Invalid OTP for {email}")
                return None
                
    logging.warning(f"User {email} not found.")
    return None