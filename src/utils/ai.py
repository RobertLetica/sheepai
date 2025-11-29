import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "data.json")

# Configure Logging (dd/mm/yyyy format)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)

if not API_KEY:
    logging.error("GEMINI_API_KEY not found in .env file.")
    exit(1)

genai.configure(api_key=API_KEY)

# List of models based on your specific access
MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-pro",
    "gemini-pro-latest"
]

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
        
        # Target common article body tags
        article_body = soup.find('article') or soup.find('div', class_='content') or soup.find('main')
        
        if article_body:
            text = article_body.get_text(separator='\n', strip=True)
        else:
            text = soup.body.get_text(separator='\n', strip=True)
            
        return text[:30000]
            
    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        return ""

def extract_tags_from_user_description(text: str) -> list:
    """
    Extracts tags from a user's description of their interests.
    """
    prompt = f"""
    Analyze the following user description and extract relevant interest tags.

    User Description: {text}

    Instructions:
    1. Extract key topics, technologies, and themes.
    2. Return ONLY a JSON list of strings.
    3. Extract as many relevant tags as possible (at least 5 if possible).

    Output Format:
    ["AI", "Machine Learning", "Finance", "Cybersecurity"]
    """

    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                }
            )

            response = model.generate_content(prompt)
            return json.loads(response.text)

        except Exception as e:
            logging.warning(f"Model {model_name} failed during user tag extraction: {e}")
            continue
    return []

def generate_tags(title: str, content_text: str) -> list:
    """
    Sends title and content to Gemini to extract tags with numeric confidence scores.
    """
    prompt = f"""
    Analyze the following article and extract relevant technical and thematic tags.
    
    Article Title: {title}
    Article Content: {content_text}
    
    Instructions:
    1. Identify key technologies, companies, malware names, concepts, or security threats mentioned.
    2. Assign a 'confidence' score as a number between 0.0 and 1.0:
       - 0.8 to 1.0: Main theme / Highly relevant.
       - 0.4 to 0.7: Secondary theme / Relevant context.
       - 0.0 to 0.3: Mentioned in passing / Low relevance.
    3. Return ONLY a JSON list of objects.
    
    Output Format:
    [
        {{"name": "ransomware", "confidence": 0.95}},
        {{"name": "linux", "confidence": 0.1}}
    ]
    """

    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                }
            )
            
            response = model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response received")

            tags = json.loads(response.text)
            logging.info(f"Success using model: {model_name}")
            return tags
            
        except Exception as e:
            logging.warning(f"Model {model_name} failed: {e}")
            continue
            
    logging.error("All available models failed to generate tags.")
    return []

def chat_with_article(query: str, article_title: str, article_content: str) -> str:
    """
    Answers a user query based on the article content.
    """
    prompt = f"""
    You are an AI assistant answering questions about a specific news article.

    Article Title: {article_title}
    Article Content: {article_content[:30000]}

    User Query: {query}

    Instructions:
    1. Answer the query based ONLY on the provided article content.
    2. If the answer is not in the article, say "I cannot answer this based on the article provided."
    3. Be concise and helpful.
    """

    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.5,
                }
            )

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logging.warning(f"Model {model_name} failed during chat: {e}")
            continue

    return "I'm having trouble connecting to the AI right now. Please try again later."

def analyze_user_interest(article: dict, user: dict) -> str:
    """
    Determines if an article is interesting to a user and generates a summary.
    Returns the summary string if interesting, or None if not.
    """
    article_title = article.get('title', '')

    # Safely extract article tags (handling both dicts and strings)
    raw_article_tags = article.get('tags', [])
    article_tags = []
    for t in raw_article_tags:
        if isinstance(t, dict):
            name = t.get('name')
            if name: article_tags.append(str(name))
        elif isinstance(t, str):
            article_tags.append(t)

    # Safely extract user tags
    raw_user_tags = user.get('tags', [])
    user_tags = []
    for t in raw_user_tags:
        if isinstance(t, dict):
            name = t.get('name')
            if name: user_tags.append(str(name))
        elif isinstance(t, str):
            user_tags.append(t)

    # Check if we have enough info
    if not user_tags and not user.get('interests_prompt'):
        # If user has no preferences, maybe skip? Or assume interested in everything?
        # Let's skip to avoid spam.
        return None

    prompt = f"""
    You are a personalized news curator.

    Article Title: {article_title}
    Article Tags: {', '.join(article_tags)}
    Article Content Snippet: {article.get('content', '')[:1000]}...

    User Interests: {', '.join(user_tags)}
    User Description: {user.get('interests_prompt', '')}

    Task:
    1. Determine if this article is highly relevant to the user's interests.
       - IMPORTANT: Use semantic matching. If a user likes "AI", they are interested in "Machine Learning", "LLMs", "Neural Networks", etc.
       - If a user likes "Cybersecurity", they are interested in "Ransomware", "Malware", "Zero-day", etc.
       - Do not rely on exact string matches.
    2. If YES, provide a short, engaging summary (max 3 sentences) explaining why it matters to them.
    3. If NO, return exactly "NOT_INTERESTING".

    Output Format:
    Just the summary text or "NOT_INTERESTING".
    """

    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.2,
                }
            )

            response = model.generate_content(prompt)
            result = response.text.strip()

            if "NOT_INTERESTING" in result:
                return None

            return result

        except Exception as e:
            logging.warning(f"Model {model_name} failed during interest analysis: {e}")
            continue

    return None

def analyze_article_by_title(target_title: str):
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
            if not current_content or len(current_content) < 50 or "Content not found" in current_content:
                logging.warning("Content appears missing. Initiating web scrape...")
                scraped_text = scrape_article_content(article.get("url"))
                if scraped_text:
                    article["content"] = scraped_text
                    current_content = scraped_text
                else:
                    logging.warning("Could not retrieve content via scraping. Proceeding with Title only.")
            
            logging.info("Sending to Gemini for tag extraction...")
            tags = generate_tags(target_title, current_content)
            
            if tags:
                article["tags"] = tags
                logging.info(f"Successfully added {len(tags)} tags.")
            else:
                logging.warning("No tags returned from API.")
            
            break

    if not article_found:
        logging.warning(f"Article with title '{target_title}' not found in {OUTPUT_FILE}")
        return

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logging.info("File updated successfully.")
    except Exception as e:
        logging.error(f"Failed to write to file: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        title_arg = " ".join(sys.argv[1:]) if len(sys.argv) > 2 else sys.argv[1]
        analyze_article_by_title(title_arg)
    else:
        print("Please provide an article title as an argument.")