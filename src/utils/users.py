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

def login(email: str, base_url: str):
    """
    1. Generates OTP.
    2. Constructs Verification Link.
    3. Sends Email.
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
    
    # Construct the link logic here
    # We append the params so the API can handle it
    verify_link = f"{base_url}/api/verify_link?email={email}&code={otp}"
    
    logging.info(f"Sending OTP to {email}...")
    success = mail.send_otp_email(to_email=email, code=otp, link=verify_link)
    
    if success:
        logging.info(f"OTP sent to {email}")
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

def validate_token(token: str):
    """
    Checks if the token is valid and returns the user object if found.
    """
    if not token:
        return None

    users = load_users()
    for user in users:
        if user.get('token') == token:
            return user

    return None

def update_user_profile(token: str, tags: list, interests_prompt: str):
    """
    Updates the user's tags and interests prompt.
    """
    users = load_users()
    user_updated = False
    updated_user = None

    for user in users:
        if user.get('token') == token:
            # Normalize existing tags to dicts if they are strings
            current_tags = []
            for t in user.get('tags', []):
                if isinstance(t, str):
                    current_tags.append({'name': t, 'confidence': 0.5})
                else:
                    current_tags.append(t)

            # Merge new tags (assuming they are strings from frontend)
            existing_names = {t['name'] for t in current_tags}
            for tag_name in tags:
                if tag_name not in existing_names:
                    current_tags.append({'name': tag_name, 'confidence': 0.5})
                    existing_names.add(tag_name)

            user['tags'] = current_tags
            user['interests_prompt'] = interests_prompt
            updated_user = user
            user_updated = True
            break

    if user_updated:
        save_users(users)
        return updated_user
    return None

def update_user_interaction(token: str, article_tags: list, action: str):
    """
    Updates user tag confidence based on interaction (like/dislike).
    article_tags: list of dicts [{'name': 'AI', 'confidence': 0.9}, ...]
    action: 'like' or 'dislike'
    """
    users = load_users()
    user_updated = False

    for user in users:
        if user.get('token') == token:
            # Normalize existing tags
            current_tags = []
            for t in user.get('tags', []):
                if isinstance(t, str):
                    current_tags.append({'name': t, 'confidence': 0.5})
                else:
                    current_tags.append(t)

            # Create a map for easy lookup
            tag_map = {t['name']: t for t in current_tags}

            for art_tag in article_tags:
                # article_tags might be dicts or strings depending on scraper format
                # scraper.py uses ai.generate_tags which returns dicts {'name':..., 'confidence':...}
                tag_name = art_tag.get('name') if isinstance(art_tag, dict) else str(art_tag)
                tag_conf = art_tag.get('confidence', 0.5) if isinstance(art_tag, dict) else 0.5

                if not tag_name: continue

                if action == 'like':
                    if tag_name in tag_map:
                        # Boost confidence
                        tag_map[tag_name]['confidence'] = min(1.0, tag_map[tag_name]['confidence'] + 0.1)
                    else:
                        # Add new tag
                        new_tag = {'name': tag_name, 'confidence': tag_conf}
                        tag_map[tag_name] = new_tag
                        current_tags.append(new_tag)

                elif action == 'dislike':
                    if tag_name in tag_map:
                        # Decrease confidence
                        tag_map[tag_name]['confidence'] = tag_map[tag_name]['confidence'] - 0.2
                        # Remove if too low
                        if tag_map[tag_name]['confidence'] <= 0.1:
                            current_tags = [t for t in current_tags if t['name'] != tag_name]
                            del tag_map[tag_name]

            user['tags'] = current_tags
            user_updated = True
            break

    if user_updated:
        save_users(users)
        return True
    return False
