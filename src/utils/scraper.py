import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
from datetime import datetime
from utils import ai  # Importing the AI module here

# Configuration
BASE_URL = "https://thehackernews.com/"
# Adjust path to save in src/ parent directory or local utils depending on preference. 
# Using relative path to match structure: src/hacker_news_articles.json
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hacker_news_articles.json")
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
        logging.error(f"Error fetching {url}: {e}")
        return None

def scrape_article_content(article_url):
    """Visits an individual article page to scrape the full content."""
    soup = get_soup(article_url)
    if not soup:
        return ""

    # Try specific THN content selectors
    content_div = soup.find('div', id='articlebody') or soup.find('div', class_='articlebody')

    if content_div:
        paragraphs = content_div.find_all('p')
        if paragraphs:
            # Join paragraphs with double newlines for readability
            return '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
        return content_div.get_text(strip=True)
    
    return ""

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
        logging.error(f"Error saving data: {e}")

def monitor_feed():
    """
    Worker function. Checks for new articles periodically.
    """
    logging.info(f"Scraper worker started. Checking every {CHECK_INTERVAL_MINUTES} minutes.")
    
    while True:
        try:
            logging.info("Checking feed...")
            
            existing_articles = load_existing_data()
            seen_urls = {art['url'] for art in existing_articles}
            
            soup = get_soup(BASE_URL)
            if not soup:
                logging.warning("Could not fetch homepage. Retrying next cycle.")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                continue

            story_links = soup.find_all('a', class_='story-link')
            new_articles_found = 0

            # Iterate through found links
            for story in story_links:
                article_url = story.get('href')

                if article_url in seen_urls:
                    continue 

                logging.info(f"New article found! Scraping: {article_url}")
                
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
                
                # --- AI INTEGRATION HERE ---
                # Call ai.py to generate tags immediately
                tags = []
                if full_content:
                    logging.info("Generating tags with AI...")
                    tags = ai.generate_tags(title, full_content)
                # ---------------------------

                new_article = {
                    "title": title,
                    "url": article_url,
                    "thumbnail": thumbnail,
                    "description": description,
                    "content": full_content,
                    "tags": tags,
                    "scraped_at": datetime.now().isoformat()
                }

                existing_articles.insert(0, new_article)
                save_data(existing_articles)
                seen_urls.add(article_url)
                new_articles_found += 1
                
                time.sleep(2)

            if new_articles_found == 0:
                logging.info("No new articles found.")
            else:
                logging.info(f"Successfully scraped {new_articles_found} new articles.")

        except Exception as e:
            logging.error(f"Critical error in scraper thread: {e}")

        time.sleep(CHECK_INTERVAL_MINUTES * 60)