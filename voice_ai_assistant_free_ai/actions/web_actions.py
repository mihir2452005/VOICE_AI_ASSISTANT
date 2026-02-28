import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

def search_web(query: str):
    """
    Searches the live internet for a given query and returns the top 3 results.
    Use this to find current events, weather, facts, or any information you don't already know.
    Args:
        query: The search term (e.g. 'weather in New York today', 'who won the superbowl 2024').
    """
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return f"No results found on the internet for '{query}'."
            
        formatted_results = f"Top Internet Search Results for '{query}':\n\n"
        for i, res in enumerate(results):
            formatted_results += f"Result {i+1}:\n"
            formatted_results += f"Title: {res.get('title', 'No Title')}\n"
            formatted_results += f"URL: {res.get('href', 'No URL')}\n"
            formatted_results += f"Snippet: {res.get('body', 'No Snippet')}\n\n"
            
        return formatted_results
    except Exception as e:
        return f"Failed to search the web for '{query}'. Error: {e}"

def read_webpage(url: str):
    """
    Scrapes a specific URL and returns the raw readable text from the webpage.
    Use this ONLY if you used `search_web` and found a specific URL that you need to read in full detail.
    Args:
        url: The full http/https URL to read.
    """
    try:
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
            
        # Pretend to be a normal browser to avoid simple bot blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        # Extract text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Truncate to avoid context limit (roughly 5000 chars)
        if len(text) > 5000:
            text = text[:5000] + "\n\n...[Content Truncated]..."
            
        return f"Content of {url}:\n\n{text}"
    except Exception as e:
        return f"Failed to read webpage {url}. Error: {e}"
