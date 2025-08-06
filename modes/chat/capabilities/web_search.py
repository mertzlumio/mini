# modes/chat/capabilities/web_search.py
# Enhanced DuckDuckGo Web Search - Gets real search results with titles, snippets, and URLs
import requests
import re
from urllib.parse import quote_plus, urljoin
from html import unescape
import time

class DuckDuckGoSearch:
    def __init__(self):
        self.session = requests.Session()
        # Use a realistic user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.last_request_time = 0
        
    def _rate_limit(self, min_interval=1.0):
        """Simple rate limiting to be respectful"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()
    
    def _clean_text(self, text):
        """Clean and decode HTML text"""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = unescape(text)
        # Clean up whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def _extract_search_results(self, html_content):
        """Extract search results from DuckDuckGo HTML"""
        print("DEBUG: Starting result extraction...")
        results = []
        
        # First, let's see what we're working with
        print(f"DEBUG: HTML content contains 'result': {'result' in html_content.lower()}")
        print(f"DEBUG: HTML content contains 'duckduckgo': {'duckduckgo' in html_content.lower()}")
        
        # Look for common result indicators
        result_indicators = ['class="result', 'data-testid="result"', '<article', 'class="web-result']
        for indicator in result_indicators:
            count = html_content.lower().count(indicator)
            print(f"DEBUG: Found {count} instances of '{indicator}'")
        
        # Pattern for search result containers
        # DuckDuckGo uses various class names, so we look for common patterns
        result_patterns = [
            r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>(?=<div[^>]*class="[^"]*result|$)',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*data-testid="result"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*web-result[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern_idx, pattern in enumerate(result_patterns):
            print(f"DEBUG: Trying pattern {pattern_idx + 1}: {pattern[:50]}...")
            matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            match_count = 0
            for match in matches:
                match_count += 1
                print(f"DEBUG: Found match {match_count} with pattern {pattern_idx + 1}")
                
                result_html = match.group(1)
                print(f"DEBUG: Match content (first 200 chars): {result_html[:200]}")
                
                # Extract title and URL
                title_patterns = [
                    r'<a[^>]*href="([^"]+)"[^>]*><span[^>]*>(.*?)</span></a>',
                    r'<h3[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a></h3>',
                    r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                    r'href="([^"]+)"[^>]*>([^<]+)</a>'
                ]
                
                title_match = None
                for title_pattern in title_patterns:
                    title_match = re.search(title_pattern, result_html, re.DOTALL)
                    if title_match:
                        print(f"DEBUG: Found title with pattern: {title_pattern[:30]}...")
                        break
                
                if title_match:
                    url = title_match.group(1)
                    title = self._clean_text(title_match.group(2))
                    
                    print(f"DEBUG: Extracted URL: {url}")
                    print(f"DEBUG: Extracted title: {title}")
                    
                    # Clean up URL (remove DuckDuckGo redirect) BEFORE validation
                    original_url = url
                    if '/l/?uddg=' in url or '//duckduckgo.com/l/?uddg=' in url:
                        url_match = re.search(r'uddg=([^&]+)', url)
                        if url_match:
                            from urllib.parse import unquote
                            url = unquote(url_match.group(1))
                            print(f"DEBUG: Cleaned URL from redirect: {url}")
                    
                    # Handle protocol-relative URLs
                    if url.startswith('//'):
                        url = 'https:' + url
                        print(f"DEBUG: Added protocol to URL: {url}")
                    
                    # Skip if URL looks invalid (after cleaning)
                    if not url.startswith(('http://', 'https://')) or 'duckduckgo.com' in url:
                        print(f"DEBUG: Skipping invalid URL: {url}")
                        continue
                    
                    # Extract snippet/description
                    snippet = ""
                    snippet_patterns = [
                        r'<span[^>]*class="[^"]*snippet[^"]*"[^>]*>(.*?)</span>',
                        r'<div[^>]*class="[^"]*snippet[^"]*"[^>]*>(.*?)</div>',
                        r'<span[^>]*>(.*?)</span>'
                    ]
                    
                    for snippet_pattern in snippet_patterns:
                        snippet_match = re.search(snippet_pattern, result_html, re.DOTALL)
                        if snippet_match:
                            snippet = self._clean_text(snippet_match.group(1))
                            if len(snippet) > 20:  # Only use substantial snippets
                                print(f"DEBUG: Found snippet: {snippet[:100]}...")
                                break
                    
                    # Clean up URL (remove DuckDuckGo redirect) - this code was moved up
                    # if '/l/?uddg=' in url:
                    #     url_match = re.search(r'/l/\?uddg=([^&]+)', url)
                    #     if url_match:
                    #         from urllib.parse import unquote
                    #         url = unquote(url_match.group(1))
                    #         print(f"DEBUG: Cleaned URL: {url}")
                    
                    if title and url:
                        result = {
                            'title': title[:100],  # Limit title length
                            'url': url,
                            'snippet': snippet[:200] if snippet else ""  # Limit snippet length
                        }
                        results.append(result)
                        print(f"DEBUG: Added result: {result}")
                        
                        if len(results) >= 5:  # Limit to 5 results
                            break
                else:
                    print("DEBUG: No title match found in this result")
            
            print(f"DEBUG: Pattern {pattern_idx + 1} found {match_count} matches, extracted {len(results)} valid results")
            
            if results:  # If we found results with one pattern, don't try others
                break
        
        print(f"DEBUG: Final result count: {len(results)}")
        return results
    
    def search(self, query, max_results=3):
        """
        Perform a web search using DuckDuckGo
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
            
        Returns:
            str: Formatted search results or error message
        """
        try:
            print(f"DEBUG: Starting search for query: '{query}'")
            self._rate_limit()
            
            # Encode the query
            encoded_query = quote_plus(query)
            print(f"DEBUG: Encoded query: '{encoded_query}'")
            
            # DuckDuckGo search URL
            search_url = f"https://duckduckgo.com/html/?q={encoded_query}&t=h_"
            print(f"DEBUG: Search URL: {search_url}")
            
            # Make the request
            print("DEBUG: Making HTTP request...")
            response = self.session.get(search_url, timeout=10)
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response content length: {len(response.text)} chars")
            
            response.raise_for_status()
            
            # Save first 1000 chars for debugging
            print(f"DEBUG: First 500 chars of response:\n{response.text[:500]}")
            
            # Extract results
            print("DEBUG: Attempting to extract search results...")
            results = self._extract_search_results(response.text)
            print(f"DEBUG: Extracted {len(results)} results")
            
            if results:
                for i, result in enumerate(results):
                    print(f"DEBUG: Result {i+1}: Title='{result['title'][:50]}...', URL='{result['url'][:80]}...'")
            
            if not results:
                print("DEBUG: No results found, checking if we got blocked or redirected...")
                # Check if we got a CAPTCHA or redirect
                if "captcha" in response.text.lower() or "blocked" in response.text.lower():
                    return f"Search temporarily blocked (CAPTCHA required). Please try again in a few minutes."
                elif "javascript" in response.text.lower() and len(response.text) < 5000:
                    return f"Search requires JavaScript. Trying alternative approach..."
                else:
                    return f"No web results found for '{query}'. HTML length: {len(response.text)}"
            
            # Format results
            formatted_results = []
            formatted_results.append(f"🔍 Search results for '{query}':\n")
            
            for i, result in enumerate(results[:max_results], 1):
                formatted_results.append(f"{i}. **{result['title']}**")
                if result['snippet']:
                    formatted_results.append(f"   {result['snippet']}")
                formatted_results.append(f"   🔗 {result['url']}\n")
            
            return "\n".join(formatted_results)
            
        except requests.exceptions.Timeout:
            return f"Search timed out for '{query}'. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Search temporarily unavailable: {str(e)}"
        except Exception as e:
            return f"Search error: {str(e)}"

# Global instance for reuse
_search_engine = None

def get_search_engine():
    """Get or create the search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = DuckDuckGoSearch()
    return _search_engine

def search_web(query: str, max_results: int = 3):
    """
    Enhanced web search function that gets real search results from DuckDuckGo.
    This replaces your previous implementation.
    
    Args:
        query (str): The search query
        max_results (int): Maximum number of results (default 3)
        
    Returns:
        str: Formatted search results with titles, snippets, and URLs
    """
    if not isinstance(query, str):
        return "Error: The search query must be a string."
    
    if not query.strip():
        return "Error: Please provide a search query."
    
    search_engine = get_search_engine()
    return search_engine.search(query.strip(), max_results)

# Fallback to instant answers if main search fails
def search_web_with_fallback(query: str, max_results: int = 3):
    """
    Search with fallback to DuckDuckGo instant answers if main search fails
    """
    # Try main search first
    main_result = search_web(query, max_results)
    
    # If main search failed, try instant answers as fallback
    if "Search error:" in main_result or "temporarily unavailable" in main_result:
        try:
            from urllib.parse import quote_plus
            import requests
            
            # Fallback to instant answers API
            encoded_query = quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            fallback_results = []
            
            if data.get('Abstract'):
                fallback_results.append(f"📄 {data['Abstract']}")
                if data.get('AbstractURL'):
                    fallback_results.append(f"🔗 {data['AbstractURL']}")
            
            if data.get('Answer'):
                fallback_results.append(f"💡 {data['Answer']}")
            
            if fallback_results:
                return f"🔍 Quick answer for '{query}':\n" + "\n".join(fallback_results)
            else:
                return main_result  # Return original error if no fallback data
                
        except Exception:
            return main_result  # Return original error if fallback fails
    
    return main_result