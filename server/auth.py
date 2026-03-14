import os
import time
from logger import log

"""
1. Read the API key from environment variable
2. Parse the X-API-Key header from the raw HTTP request
3. Check if the key is valid
4. Check if the key is rate limited
5. Return a result the API can use
"""

VALID_API_KEY = os.environ.get("PULSE_API_KEY", "dev-key-123")
request_counts = {}
RATE_LIMIT = 100

def get_api_key_from_req(raw_req):
    """
    Splits the HTTP request to get the API Key
    """
    lines = raw_req.split("\r\n")
    for line in lines:
        if line.startswith("X-API-Key:"):
            return line.split(": ", 1)[1].strip()
        
    return None


def is_rate_limited(api_key):
    """
    Checks for rate liminting, if the amount of api req from client exceeds limit
    """

    now = time.time()
    window_start = now - 60

    # get the history for the api key, default empty list
    history = request_counts.get(api_key, [])

    # keep only the times that are within the last 60 seconds
    history = [t for t in history if t > window_start]

    if len(history) >= RATE_LIMIT:
        return True

    history.append(now)
    request_counts[api_key] = history
    return False

def validate_req(raw_req):
    """
    Takes in raw api key, parses, and validates it
    """
    api_key = get_api_key_from_req(raw_req)

    first_line = raw_req.split("\r\n")[0]
    if first_line.startswith("OPTIONS"):
        return True, 200, "ok"

    if api_key is None:
        log("WARN", "Missing API Key")
        return False, 401, "missing api key"
    
    if api_key != VALID_API_KEY:
        log("WARN", "Invalid API Key")
        return False, 401, "invalid api key"
    
    if is_rate_limited(api_key):
        log("WARN", "Rate Limit Exceeded", api_key=api_key)
        return False, 429, "rate limit exceeded"
    
    return True, 200, "ok"
