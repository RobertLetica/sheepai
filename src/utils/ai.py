import os
import json
import logging
import typing
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "data.json")

# Configure Logging (dd/mm/yyyy format as requested)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)

if not API_KEY:
    logging.error("GEMINI_API_KEY not found in .env file.")
    exit(1)

genai.configure(api_key=API_KEY)

# Initialize Model
# Using gemini-1.5-flash for speed and efficiency with text analysis
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "response_mime_type": "application/json",
        "temperature": 0.2,
    }
)

def scrape_article_content(url: str) -> str:
    """
    Visits the URL to extract text content if missing from JSON.
    """
    logging.info(f"Scraping content from: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Basic extraction - adjust based on specific site structure if needed
        # This targets common article body tags
        article_body = soup.find('article') or soup.find('div', class_='content') or soup.find('main')
        
        if article_body:
            return article_body.get_text(separator='\n', strip=True)
        else:
            # Fallback to body text if structure is unclear
            return soup.body.get_text(separator='\n', strip=True)
            
    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        return ""

def generate_tags(title: str, content_text: str) -> list:
    """
    Sends title and content to Gemini to extract tags with confidence scores.
    """
    prompt = f"""
    Analyze the following article and extract relevant technical and thematic tags.
    
    Article Title: {title}
    Article Content: {content_text}
    
    Instructions:
    1. Identify key technologies, companies, malware names, concepts, or security threats mentioned.
    2. Assign a 'confidence' score to each tag:
       - "high": If this is a main theme or subject of the article.
       - "low": If this is merely mentioned in passing or as a minor detail.
    3. Return ONLY a JSON list of objects.
    
    Output Format:
    [
        {{"name": "example_tag", "confidence": "high"}},
        {{"name": "another_tag", "confidence": "low"}}
    ]
    """

    try:
        response = model.generate_content(prompt)
        # Parse the JSON string returned by Gemini
        tags = json.loads(response.text)
        return tags
    except Exception as e:
        logging.error(f"Gemini analysis failed: {e}")
        return []

def analyze_article_by_title(target_title: str):
    """
    Main function to find an article by title in the JSON file, 
    ensure it has content, analyze it with Gemini, and save the tags.
    """
    if not os.path.exists(OUTPUT_FILE):
        logging.error(f"File {OUTPUT_FILE} not found.")
        return

    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from {OUTPUT_FILE}")
        return

    article_found = False

    for article in data:
        if article.get("title") == target_title:
            article_found = True
            logging.info(f"Processing: {target_title}")

            # Check if content needs scraping
            current_content = article.get("content", "")
            if not current_content or current_content.strip() == "Content not found." or "Content not found" in current_content:
                logging.warning("Content missing. Initiating web scrape...")
                scraped_text = scrape_article_content(article.get("url"))
                if scraped_text:
                    article["content"] = scraped_text
                    current_content = scraped_text
                else:
                    logging.warning("Could not retrieve content via scraping. Skipping analysis.")
                    continue

            # Analyze with Gemini
            logging.info("Sending to Gemini for tag extraction...")
            tags = generate_tags(target_title, current_content)
            
            if tags:
                article["tags"] = tags
                logging.info(f"Successfully added {len(tags)} tags.")
            else:
                logging.warning("No tags returned from API.")
            
            break # Stop after finding the specific article

    if not article_found:
        logging.warning(f"Article with title '{target_title}' not found in {OUTPUT_FILE}")
        return

    # Write updates back to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logging.info("File updated successfully.")
    except Exception as e:
        logging.error(f"Failed to write to file: {e}")

# Example Usage Block
if __name__ == "__main__":
    import sys
    
    # If run from command line with an argument: python ai.py "Article Title"
    if len(sys.argv) > 1:
        title_arg = sys.argv[1]
        analyze_article_by_title(title_arg)
    else:
        # For testing purposes, you can manually run a title from your example json here
        # or loop through all items in the file if you prefer.
        print("Please provide an article title as an argument.")
        print('Example: python ai.py "The Ultimate WSUS Replacement Guide for Modern IT Teams"')