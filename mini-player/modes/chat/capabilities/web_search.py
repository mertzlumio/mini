# Enhanced web_search.py with SINGLE summarization call to fix connection issues
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
            
            # Use a fresh session for each content request to avoid connection pool issues
            with requests.Session() as content_session:
                content_session.headers.update(self.session.headers)
                response = content_session.get(url, timeout=10)
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
    
    def _summarize_all_content_with_mistral(self, content_sources, query):
        """
        FIXED: Use Mistral to summarize ALL content in a SINGLE API call
        This eliminates multiple API calls that cause connection issues
        """
        try:
            from ..utils.api_client import call_mistral_api
            
            # Combine all content sources into one text block
            combined_content = []
            for i, (title, content, url) in enumerate(content_sources, 1):
                combined_content.append(f"=== SOURCE {i}: {title} ===")
                combined_content.append(f"URL: {url}")
                combined_content.append(f"CONTENT: {content}")
                combined_content.append("=" * 50)
            
            full_content = "\n\n".join(combined_content)
            
            # Single API call to analyze all content at once
            summary_prompt = [
                {
                    "role": "system",
                    "content": f"You are helping to analyze web search results. The user searched for '{query}'. I've gathered content from multiple sources. Please provide a comprehensive summary that:\n1. Answers the user's query directly\n2. Synthesizes information from all sources\n3. Highlights key findings and relevant details\n4. Organizes the information clearly\n5. Cites which sources contain which information"
                },
                {
                    "role": "user",
                    "content": f"Please analyze and summarize these search results for the query '{query}':\n\n{full_content}\n\nProvide a comprehensive summary that answers what the user was looking for, drawing from all the sources."
                }
            ]
            
            print(f"DEBUG: Making SINGLE summarization call with {len(content_sources)} sources")
            response = call_mistral_api(summary_prompt)
            summary = response.get('content', '')
            
            print(f"DEBUG: Generated comprehensive summary of {len(summary)} characters")
            return summary
            
        except Exception as e:
            print(f"DEBUG: Failed to generate summary: {e}")
            # Fallback: create a simple combined summary
            fallback_parts = []
            for title, content, url in content_sources:
                snippet = content[:200] + "..." if len(content) > 200 else content
                fallback_parts.append(f"**{title}**: {snippet}")
            return "\n\n".join(fallback_parts)
    
    def _extract_search_results(self, html_content):
        """Extract search results from DuckDuckGo HTML (existing method)"""
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
        FIXED: Enhanced search with SINGLE summarization call
        
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
            
            # FIXED: Enhanced mode with SINGLE summarization call
            print(f"DEBUG: Extracting content from {max_results} sources...")
            
            # Step 1: Collect all content from all sources (no API calls yet)
            content_sources = []
            for i, result in enumerate(results[:max_results], 1):
                print(f"DEBUG: Processing source {i}/{max_results}: {result['title']}")
                
                # Extract page content
                content = self._extract_page_content(result['url'])
                
                if content:
                    content_sources.append((result['title'], content, result['url']))
                elif result['snippet']:
                    # Use snippet as fallback
                    content_sources.append((result['title'], result['snippet'], result['url']))
            
            if not content_sources:
                return f"🔍 Search completed for '{query}', but no content could be extracted from the results."
            
            # Step 2: Make SINGLE API call to summarize all content
            print(f"DEBUG: Making single summarization call for {len(content_sources)} sources")
            comprehensive_summary = self._summarize_all_content_with_mistral(content_sources, query)
            
            # Step 3: Format the final response
            formatted_results = [f"🔍 **{query}** - Comprehensive Search Analysis:\n"]
            formatted_results.append(comprehensive_summary)
            formatted_results.append(f"\n📚 **Sources analyzed:**")
            
            for i, (title, _, url) in enumerate(content_sources, 1):
                formatted_results.append(f"{i}. {title}")
                formatted_results.append(f"   🔗 {url}")
            
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
    FIXED: Enhanced web search with SINGLE summarization call
    
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