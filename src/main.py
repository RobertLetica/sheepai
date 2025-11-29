import threading
import time
import logging
import sys
from dotenv import load_dotenv
from utils import scraper
from utils import users

# Load environment variables
load_dotenv()

# Configure Logging (Global configuration)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)

def input_loop():
    """Simple CLI for interacting with the system"""
    print("\n--- SheepAI Command Line Interface ---")
    print("Commands: login, exit")
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "exit":
                print("Exiting CLI...")
                # We exit the whole program
                os._exit(0)
                
            elif cmd == "login":
                email = input("Enter your email: ").strip()
                if not email:
                    print("Email is required.")
                    continue
                    
                print(f"Sending OTP to {email}...")
                if users.login(email):
                    print("OTP sent! Check your inbox.")
                    
                    otp_code = input("Enter OTP Code: ").strip()
                    token = users.verify_otp(email, otp_code)
                    
                    if token:
                        print(f"Login Successful! Your Access Token: {token}")
                    else:
                        print("Login Failed: Invalid OTP.")
                else:
                    print("Error sending OTP.")
            
        except KeyboardInterrupt:
            print("\nStopping...")
            os._exit(0)
        except Exception as e:
            logging.error(f"Error in CLI: {e}")

if __name__ == "__main__":
    import os
    logging.info("Starting SheepAI Feed Monitor...")

    # Start the scraper in a background thread
    # daemon=True ensures the thread closes when the main program exits
    scraper_thread = threading.Thread(target=scraper.monitor_feed, daemon=True)
    scraper_thread.start()
    
    # Run the input loop in the main thread
    input_loop()