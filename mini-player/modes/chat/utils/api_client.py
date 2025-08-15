# Updated modes/chat/api_client.py - FIXED Rate Limiting
import requests
import time
import threading  
from config import MISTRAL_API_KEY, MISTRAL_URL, get_text_model, get_vision_model
from ..prompts.composer import get_system_prompt  # Updated import
from ..prompts.tools import get_mistral_tools      # Updated import

class RateLimiter:
    """Centralized rate limiter for all API calls"""
    def __init__(self):
        self.last_call_time = 0
        self.min_interval = 2.0  # Increased from 1.5 to be safer
        self.lock = threading.Lock()  # Thread safety
    
    def wait_if_needed(self, custom_interval=None):
        """Wait if needed to respect rate limits"""
        with self.lock:
            interval = custom_interval or self.min_interval
            now = time.time()
            elapsed = now - self.last_call_time
            
            if elapsed < interval:
                wait_time = interval - elapsed
                print(f"DEBUG: Rate limiting - waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            
            self.last_call_time = time.time()

# Global rate limiter instance
import threading
_rate_limiter = RateLimiter()

def call_mistral_api(history, min_interval=2.0):
    """
    Standard Mistral API call for text-only conversations
    Uses your regular text model (mistral-medium)
    FIXED: Proper rate limiting
    """
    print(f"DEBUG: API call requested - waiting for rate limit...")
    _rate_limiter.wait_if_needed(min_interval)

    # Use TEXT model for regular chat
    text_model = get_text_model()
    print(f"DEBUG: Using text model: {text_model}")

    messages = [{"role": "system", "content": get_system_prompt()}]
    for msg in history:
        if msg.get("role") in ["user", "assistant", "tool"]:
            messages.append(msg)

    data = {
        "model": text_model,  # mistral-medium
        "messages": messages,
        "tools": get_mistral_tools(),
        "tool_choice": "auto"
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            print(f"DEBUG: Making text API call (attempt {attempt + 1}) at {time.time()}")
            response = requests.post(MISTRAL_URL, headers=headers, json=data, timeout=30)
            
            if response.status_code == 429:
                print(f"DEBUG: Hit rate limit (429), waiting longer...")
                time.sleep(5)
                _rate_limiter.wait_if_needed(5.0)
                continue  # Retry
            
            response.raise_for_status()
            print(f"DEBUG: Text API call successful")
            return response.json()['choices'][0]['message']
            
        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                print(f"DEBUG: Rate limit hit, retrying...")
                time.sleep(retry_delay * (attempt + 1))
                continue
            print(f"DEBUG: HTTP error: {e}")
            # For other HTTP errors, we might not want to retry
            return {"role": "assistant", "content": f"An API error occurred: {e}"}

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"DEBUG: Connection error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            return {"role": "assistant", "content": "I'm having trouble connecting to the server. Please check your internet connection."
            }
        
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: A request exception occurred: {e}")
            # For other request-related errors, break and return an error
            return {"role": "assistant", "content": f"An unexpected network error occurred: {e}"}

    return {"role": "assistant", "content": "The request failed after multiple retries. Please try again later."}

def call_mistral_vision_api(history, image_base64, min_interval=3.0):
    """
    FIXED: Mistral Vision API call for screen analysis
    Uses separate vision model (pixtral-12b-latest)
    FIXED: Proper rate limiting with longer interval for vision
    """
    print(f"DEBUG: Vision API call requested - waiting for rate limit...")
    _rate_limiter.wait_if_needed(min_interval)  # Vision calls need more spacing

    # Use VISION model for screen analysis
    vision_model = get_vision_model()
    print(f"DEBUG: Using vision model: {vision_model}")
    
    # FIXED: Simpler message structure for vision
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I've captured my current screen. Please analyze what you see and help me understand the content. Be specific about what applications, interfaces, or content you can identify."
                },
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]

    # FIXED: Simplified request structure - no tools for vision to avoid conflicts
    data = {
        "model": vision_model,
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.1  # Lower temperature for more consistent analysis
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    retry_delay = 3  # seconds for vision API

    for attempt in range(max_retries):
        try:
            print(f"DEBUG: Making vision API call with {vision_model} (attempt {attempt + 1}) at {time.time()}")
            response = requests.post(MISTRAL_URL, headers=headers, json=data, timeout=45)
            
            if response.status_code == 429:
                print("DEBUG: Vision API hit rate limit (429), waiting longer...")
                time.sleep(8)
                _rate_limiter.wait_if_needed(8.0)
                continue # Retry
            
            response.raise_for_status()
            
            result = response.json()
            print(f"DEBUG: Vision API call successful")
            return result['choices'][0]['message']
            
        except requests.exceptions.HTTPError as e:
            print(f"DEBUG: Vision API HTTP error: {e}")
            if "429" in str(e):
                time.sleep(retry_delay * (attempt + 1))
                continue
            return {
                "role": "assistant", 
                "content": f"I captured your screen but encountered an API error while analyzing the visual content: {str(e)}."
            }
        
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"DEBUG: Vision API connection error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            return {
                "role": "assistant",
                "content": "I'm having trouble connecting to the server to analyze the screen. Please check your internet connection."
            }

        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Vision API request exception: {e}")
            return {
                "role": "assistant",
                "content": f"An unexpected network error occurred while analyzing the screen: {e}"
            }

    return {
        "role": "assistant",
        "content": "The vision request failed after multiple retries. Please try again later."
    }

def supports_vision():
    """Check if vision is available"""
    try:
        from config import supports_vision as config_supports_vision
        return config_supports_vision()
    except ImportError:
        return False

# Debug function to check rate limiting
def debug_rate_limiting():
    """Debug function to check rate limiter state"""
    print(f"Rate limiter state:")
    print(f"  Last call time: {_rate_limiter.last_call_time}")
    print(f"  Current time: {time.time()}")
    print(f"  Time since last call: {time.time() - _rate_limiter.last_call_time:.2f}s")
    print(f"  Min interval: {_rate_limiter.min_interval}s")