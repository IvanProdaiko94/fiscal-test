"""
HTTP client for making requests with retry logic and error handling.
"""

import requests
from typing import Optional
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HTTPClient:
    """Centralized HTTP client for making requests with retry logic and error handling."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Track problematic URLs to skip them quickly
        self.problematic_urls = set()
    
    def make_request(self, url: str, timeout: int = 15, **kwargs) -> Optional[requests.Response]:
        """Make a request with retry logic and better error handling."""
        # Quick skip for known problematic URLs
        if url in self.problematic_urls:
            logger.debug(f"Skipping known problematic URL: {url}")
            return None
            
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=timeout, **kwargs)
                response.raise_for_status()
                return response
                
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ReadTimeout) as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}) for {url}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {max_retries} attempts for {url}: {e}")
                    # Mark URL as problematic for future requests
                    self.problematic_urls.add(url)
                    return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {url}: {e}")
                # Mark URL as problematic for future requests
                self.problematic_urls.add(url)
                return None
        
        return None
    
    def get_session(self) -> requests.Session:
        """Get the underlying requests session for advanced usage."""
        return self.session
