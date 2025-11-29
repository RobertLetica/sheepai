import json
import random
import time

# File path must match your scraper's output
DATA_FILE = "hacker_news_articles.json"

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def mock_ai_analysis(text):
    """
    REPLACE THIS FUNCTION with your actual AI logic later.
    Input: Article text
    Output: List of tag objects
    """
    # Mock logic: look for keywords and assign random confidence
    keywords = ["malware", "ransomware", "iot", "zero-day", "phishing", "linux", "windows"]
    found_tags = []
    
    text_lower = text.lower()
    
    for word in keywords:
        if word in text_lower:
            # Simulate AI confidence score
            confidence = round(random.uniform(0.70, 0.99), 2)
            found_tags.append({"tag": word, "confidence": confidence})
    
    # If no keywords found, mark as generic
    if not found_tags:
         found_tags.append({"tag": "general-security", "confidence": 0.50})
         
    return found_tags

def process_tags():
    print("Loading database...")
    articles = load_data()
    
    updates_count = 0
    
    for article in articles:
        # Check if 'tags' key exists, if not create it
        if "tags" not in article:
            article["tags"] = []

        # Only analyze if tags are empty (avoid re-analyzing)
        if not article["tags"]:
            print(f"Analyzing: {article.get('title', 'Unknown')}...")
            
            # Combine title and content for better context
            full_text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
            
            # CALL YOUR AI HERE
            new_tags = mock_ai_analysis(full_text)
            
            article["tags"] = new_tags
            updates_count += 1
            print(f" -> Assigned tags: {new_tags}")

    if updates_count > 0:
        print(f"Saving {updates_count} updated articles...")
        save_data(articles)
    else:
        print("No new articles to analyze.")

if __name__ == "__main__":
    # You can run this in a loop or a cron job independently of the scraper
    process_tags()