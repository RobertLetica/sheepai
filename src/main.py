import threading
import time
import logging
import os
from dotenv import load_dotenv
from utils import scraper

# Load environment variables
load_dotenv()

# Configure Logging (Global configuration)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)

if __name__ == "__main__":
    logging.info("Starting SheepAI Feed Monitor...")

    # Start the scraper in a background thread
    # daemon=True ensures the thread closes when the main program exits
    scraper_thread = threading.Thread(target=scraper.monitor_feed, daemon=True)
    scraper_thread.start()

    try:
        # Keep the main process alive to allow the daemon thread to run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping SheepAI...")