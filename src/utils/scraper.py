import requests
from bs4 import BeautifulSoup
import json
import time
import threading
import os
from datetime import datetime
from utils import ai

# Configuration
BASE_URL = "https://thehackernews.com/"
OUTPUT_FILE = "hacker_news_articles.json"
CHECK_INTERVAL_MINUTES = 5
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"[!] Error fetching {url}: {e}")
        return None

def scrape_article_content(article_url):
    """Visits an individual article page to scrape the full content."""
    soup = get_soup(article_url)
    if not soup:
        return "Failed to retrieve content."

    # Try specific THN content selectors
    content_div = soup.find('div', id='articlebody') or soup.find('div', class_='articlebody')

    if content_div:
        paragraphs = content_div.find_all('p')
        if paragraphs:
            # Join paragraphs with double newlines for readability
            return '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
        return content_div.get_text(strip=True)
    
    return "Content not found."

def load_existing_data():
    """Loads existing JSON to prevent duplicates."""
    if not os.path.exists(OUTPUT_FILE):
        return []
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_data(data):
    """Saves the list of articles to JSON."""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"[!] Error saving data: {e}")

def monitor_feed():
    """
    Worker function to run in a thread. 
    Checks for new articles periodically.
    """
    print(f"[*] Worker started. Checking every {CHECK_INTERVAL_MINUTES} minutes.")
    
    while True:
        try:
            print(f"\n[*] Checking feed at {datetime.now().strftime('%H:%M:%S')}...")
            
            # 1. Load current database (in case other processes modified it)
            existing_articles = load_existing_data()
            seen_urls = {art['url'] for art in existing_articles}
            
            # 2. Fetch Homepage
            soup = get_soup(BASE_URL)
            if not soup:
                print("[!] Could not fetch homepage. Retrying next cycle.")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                continue

            # 3. Find Article Links
            story_links = soup.find_all('a', class_='story-link')
            new_articles_found = 0

            # Iterate through found links (latest first usually)
            for story in story_links:
                article_url = story.get('href')

                if article_url in seen_urls:
                    continue # Skip if we already have it

                # 4. Scrape New Article
                print(f"[+] New article found! Scraping: {article_url}")
                
                # Extract Metadata
                title_tag = story.find(class_='home-title')
                title = title_tag.get_text(strip=True) if title_tag else "No Title"

                desc_tag = story.find(class_='home-desc')
                description = desc_tag.get_text(strip=True) if desc_tag else "No Description"

                img_tag = story.find('img')
                thumbnail = "No Image"
                if img_tag:
                    thumbnail = img_tag.get('data-src') or img_tag.get('src')

                # Extract Full Content
                full_content = scrape_article_content(article_url)

                # Construct Object
                new_article = {
                    "title": title,
                    "url": article_url,
                    "thumbnail": thumbnail,
                    "description": description,
                    "content": full_content,
                    "tags": [],
                    "scraped_at": datetime.now().isoformat()
                }

                # 5. Update Data
                # Add to memory and save immediately so we don't lose it if crash
                existing_articles.insert(0, new_article) # Add to top
                save_data(existing_articles)
                seen_urls.add(article_url)
                new_articles_found += 1
                
                # Politeness delay between individual article scrapes
                time.sleep(2)

            if new_articles_found == 0:
                print("[-] No new articles found.")
            else:
                print(f"[*] Successfully scraped {new_articles_found} new articles.")

        except Exception as e:
            print(f"[!] Critical error in worker thread: {e}")

        # Wait for the next cycle
        time.sleep(CHECK_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    # Create the worker thread
    # daemon=True means the thread will die when the main program exits
    worker_thread = threading.Thread(target=monitor_feed, daemon=True)
    worker_thread.start()

    try:
        # Keep the main program alive to let the daemon thread work
        print("Main program running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping worker and exiting...")