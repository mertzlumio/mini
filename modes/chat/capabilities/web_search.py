# # modes/chat/capabilities/web_search.py
# import requests
# import json

# def search_web(query: str, max_results: int = 3):
#     """Real web search using DuckDuckGo Instant Answer API"""
#     try:
#         # DuckDuckGo Instant Answer API
#         url = "https://api.duckduckgo.com/"
#         params = {
#             'q': query,
#             'format': 'json',
#             'no_html': '1',
#             'skip_disambig': '1'
#         }
        
#         response = requests.get(url, params=params, timeout=10)
#         data = response.json()
        
#         # Extract relevant information
#         results = []
        
#         # Abstract/summary
#         if data.get('Abstract'):
#             results.append(f"Summary: {data['Abstract']}")
            
#         # Related topics
#         for topic in data.get('RelatedTopics', [])[:max_results]:
#             if isinstance(topic, dict) and topic.get('Text'):
#                 results.append(f"• {topic['Text']}")
        
#         if results:
#             return "\n".join(results)
#         else:
#             return f"No specific information found for '{query}'. Try a more specific search term."
            
#     except Exception as e:
#         return f"Search temporarily unavailable: {str(e)}"

"""---------------------------------------------------------------------------------------------------------------------------"""

# modes/chat/capabilities/web_search.py
import requests
import json
from urllib.parse import quote_plus

def search_web(query: str, max_results: int = 3):
    """
    Real web search using DuckDuckGo Instant Answer API.
    This replaces the placeholder implementation.
    """
    if not isinstance(query, str):
        return "Error: The search query must be a string."

    try:
        # DuckDuckGo Instant Answer API
        encoded_query = quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Get abstract/summary if available
        if data.get('Abstract'):
            results.append(f"📄 {data['Abstract']}")
            if data.get('AbstractURL'):
                results.append(f"🔗 Source: {data['AbstractURL']}")
        
        # Get answer if it's a direct question
        if data.get('Answer'):
            results.append(f"💡 {data['Answer']}")
        
        # Get related topics
        related_topics = data.get('RelatedTopics', [])
        if isinstance(related_topics, list):
            topic_count = 0
            for topic in related_topics:
                if topic_count >= max_results:
                    break
                    
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append(f"• {topic['Text']}")
                    topic_count += 1
        
        # If we have results, return them
        if results:
            return "\n".join(results)
        else:
            return f"No specific information found for '{query}'. Try a more specific search term."
            
    except requests.exceptions.Timeout:
        return f"Search timed out for '{query}'. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Search temporarily unavailable: {str(e)}"
    except Exception as e:
        return f"Search error: {str(e)}"