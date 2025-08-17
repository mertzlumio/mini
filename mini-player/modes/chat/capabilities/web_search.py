# Enhanced web_search.py with content extraction and summarization
import requests
import re
from urllib.parse import quote_plus, urljoin
from html import unescape
import time

class DuckDuckGoSearch:
    def __init__(self):
        self.session = requests.Session()
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
        text = re.sub(r'<[^>]+>', '', text)
        text = unescape(text)
        text = ' '.join(text.split())
        return text.strip()
    
    def _extract_page_content(self, url, max_content_length=2000):
        """Extract main content from a webpage"""
        try:
            print(f"DEBUG: Fetching content from {url}")
            self._rate_limit(0.5)  # Be respectful
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            html = response.text
            
            # Try to extract main content using common patterns
            content_patterns = [
                # Article tags
                r'<article[^>]*>(.*?)</article>',
                # Main content areas
                r'<main[^>]*>(.*?)</main>',
                # Content divs
                r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*entry[^"]*"[^>]*>(.*?)</div>',
                # Paragraph collections
                r'<div[^>]*>((?:<p[^>]*>.*?</p>\s*){3,})</div>',
            ]
            
            extracted_content = ""
            
            for pattern in content_patterns:
                matches = re.finditer(pattern, html, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    content = self._clean_text(match.group(1))
                    if len(content) > len(extracted_content) and len(content) > 200:
                        extracted_content = content
                        break
                if extracted_content:
                    break
            
            # Fallback: extract all paragraph text
            if not extracted_content:
                paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
                content_parts = []
                for p in paragraphs:
                    clean_p = self._clean_text(p)
                    if len(clean_p) > 50:  # Only meaningful paragraphs
                        content_parts.append(clean_p)
                    if len('\n'.join(content_parts)) > max_content_length:
                        break
                extracted_content = '\n\n'.join(content_parts)
            
            # Limit content length
            if len(extracted_content) > max_content_length:
                extracted_content = extracted_content[:max_content_length] + "..."
            
            print(f"DEBUG: Extracted {len(extracted_content)} characters from {url}")
            return extracted_content
            
        except Exception as e:
            print(f"DEBUG: Failed to extract content from {url}: {e}")
            return ""
    
    def _summarize_with_mistral(self, content, query):
        """Use Mistral to summarize the content based on the user's query"""
        try:
            from ..utils.api_client import call_mistral_api
            
            summary_prompt = [
                {
                    "role": "system",
                    "content": f"You are helping to summarize web content. The user searched for '{query}'. Extract and summarize the most relevant information from the content that answers their query. Be concise but informative. Focus on what the user was looking for."
                },
                {
                    "role": "user",
                    "content": f"Content to summarize:\n\n{content}\n\nUser's query: {query}\n\nPlease provide a focused summary that answers what the user was searching for."
                }
            ]
            
            response = call_mistral_api(summary_prompt)
            summary = response.get('content', '')
            
            print(f"DEBUG: Generated summary of {len(summary)} characters")
            return summary
            
        except Exception as e:
            print(f"DEBUG: Failed to generate summary: {e}")
            return content[:500] + "..." if len(content) > 500 else content
    
    def _extract_search_results(self, html_content):
        """Extract search results from DuckDuckGo HTML (existing method)"""
        # ... your existing extraction code here ...
        # (I'll keep it as-is since it's working)
        results = []
        
        result_patterns = [
            r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>(?=<div[^>]*class="[^"]*result|$)',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*data-testid="result"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*web-result[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in result_patterns:
            matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                result_html = match.group(1)
                
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
                        break
                
                if title_match:
                    url = title_match.group(1)
                    title = self._clean_text(title_match.group(2))
                    
                    # Clean up URL
                    if '/l/?uddg=' in url:
                        url_match = re.search(r'uddg=([^&]+)', url)
                        if url_match:
                            from urllib.parse import unquote
                            url = unquote(url_match.group(1))
                    
                    if url.startswith('//'):
                        url = 'https:' + url
                    
                    if not url.startswith(('http://', 'https://')) or 'duckduckgo.com' in url:
                        continue
                    
                    # Extract snippet
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
                            if len(snippet) > 20:
                                break
                    
                    if title and url:
                        result = {
                            'title': title[:100],
                            'url': url,
                            'snippet': snippet[:200] if snippet else ""
                        }
                        results.append(result)
                        
                        if len(results) >= 5:
                            break
            
            if results:
                break
        
        return results
    
    def search_with_content(self, query, max_results=2, extract_content=True):
        """
        Enhanced search that extracts and summarizes actual page content
        
        Args:
            query (str): Search query
            max_results (int): Max results to process (fewer for content extraction)
            extract_content (bool): Whether to extract and summarize page content
        """
        try:
            print(f"DEBUG: Enhanced search for: '{query}' (content extraction: {extract_content})")
            self._rate_limit()
            
            # Get search results
            encoded_query = quote_plus(query)
            search_url = f"https://duckduckgo.com/html/?q={encoded_query}&t=h_"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            results = self._extract_search_results(response.text)
            
            if not results:
                return f"No search results found for '{query}'"
            
            if not extract_content:
                # Return traditional search results
                formatted_results = [f"🔍 Search results for '{query}':\n"]
                for i, result in enumerate(results[:max_results], 1):
                    formatted_results.append(f"{i}. **{result['title']}**")
                    if result['snippet']:
                        formatted_results.append(f"   {result['snippet']}")
                    formatted_results.append(f"   🔗 {result['url']}\n")
                return "\n".join(formatted_results)
            
            # Enhanced mode: extract and summarize content
            formatted_results = [f"🔍 **{query}** - Enhanced Search Results:\n"]
            
            for i, result in enumerate(results[:max_results], 1):
                formatted_results.append(f"## {i}. {result['title']}")
                
                # Extract page content
                content = self._extract_page_content(result['url'])
                
                if content:
                    # Summarize with Mistral
                    summary = self._summarize_with_mistral(content, query)
                    formatted_results.append(f"**Summary:** {summary}")
                elif result['snippet']:
                    formatted_results.append(f"**Description:** {result['snippet']}")
                
                formatted_results.append(f"🔗 Source: {result['url']}\n")
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            return f"Search error: {str(e)}"

# Global instance
_search_engine = None

def get_search_engine():
    global _search_engine
    if _search_engine is None:
        _search_engine = DuckDuckGoSearch()
    return _search_engine

def search_web(query: str, max_results: int = 2, with_content: bool = True):
    """
    Enhanced web search with content extraction and summarization
    
    Args:
        query (str): Search query
        max_results (int): Number of results (default 2 for content mode, 3 for basic)
        with_content (bool): Whether to extract and summarize page content
    """
    if not isinstance(query, str) or not query.strip():
        return "Error: Please provide a valid search query."
    
    search_engine = get_search_engine()
    
    # Detect if user wants basic search results
    basic_keywords = ['link', 'url', 'website', 'source', 'find me']
    wants_basic = any(keyword in query.lower() for keyword in basic_keywords)
    
    if wants_basic:
        with_content = False
        max_results = 3
    
    return search_engine.search_with_content(query.strip(), max_results, with_content)

# Backward compatibility
def search_web_basic(query: str, max_results: int = 3):
    """Basic search that just returns links (for backward compatibility)"""
    return search_web(query, max_results, with_content=False)