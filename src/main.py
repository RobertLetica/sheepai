import threading
import time
import logging
import sys
import os
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

def input_loop():
    print("\n--- SheepAI CLI ---")
    print("Commands: login, exit")
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "exit":
                print("Stopping...")
                os._exit(0)
                
            elif cmd == "login":
                email = input("Enter email: ").strip()
                if users.login(email):
                    print("Check your email for the code!")
                    code = input("Enter OTP: ").strip()
                    token = users.verify_otp(email, code)
                    if token:
                        print(f"SUCCESS! Token: {token}")
                    else:
                        print("FAILED: Invalid code.")
                else:
                    print("Could not send email. Check logs.")
                    
        except KeyboardInterrupt:
            os._exit(0)
        except Exception as e:
            logging.error(f"Error: {e}")

if __name__ == "__main__":
    logging.info("Starting SheepAI...")

    # Start scraper in background
    scraper_thread = threading.Thread(target=scraper.monitor_feed, daemon=True)
    scraper_thread.start()

    # Run CLI in foreground
    input_loop()