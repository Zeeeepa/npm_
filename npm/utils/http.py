"""HTTP utilities with retry logic and error handling."""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional


class HttpError(Exception):
    """Base exception for HTTP errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(HttpError):
    """Exception for rate limit errors (HTTP 429)."""
    pass


# Global session instance (lazy-initialized)
_session: Optional[requests.Session] = None


def create_session(
    user_agent: str = None,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (429, 500, 502, 503, 504)
) -> requests.Session:
    """Create a requests session with retry logic.
    
    Args:
        user_agent: Custom user agent string (uses default if None).
        max_retries: Maximum number of retry attempts.
        backoff_factor: Backoff factor for exponential backoff.
        status_forcelist: HTTP status codes that trigger a retry.
        
    Returns:
        Configured requests.Session instance.
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set default headers
    if user_agent is None:
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    
    session.headers.update({"User-Agent": user_agent})
    
    return session


def get_session() -> requests.Session:
    """Get or create the global HTTP session with configuration.
    
    Lazy-initializes session with config from environment.
    
    Returns:
        Configured requests.Session instance.
    """
    global _session
    if _session is None:
        from npm.config import get_config
        config = get_config()
        _session = create_session(user_agent=config.user_agent)
    return _session


def reset_session() -> None:
    """Reset the global session (useful for testing)."""
    global _session
    _session = None


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    session: Optional[requests.Session] = None
) -> Dict[str, Any]:
    """Make a GET request and return JSON response.
    
    Args:
        url: URL to fetch.
        params: Query parameters.
        headers: Additional headers.
        timeout: Request timeout in seconds (uses config default if None).
        session: Requests session (uses global session if None).
        
    Returns:
        Parsed JSON response as dict.
        
    Raises:
        HttpError: If request fails.
        RateLimitError: If rate limit is hit (HTTP 429).
    """
    if session is None:
        session = get_session()
    
    if timeout is None:
        from npm.config import get_config
        timeout = get_config().request_timeout
    
    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        
        if response.status_code == 429:
            raise RateLimitError(
                f"Rate limit exceeded for {url}",
                status_code=429
            )
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout as e:
        raise HttpError(f"Request timeout for {url}: {e}")
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        raise HttpError(f"Request failed for {url}: {e}", status_code=status_code)
    except ValueError as e:
        raise HttpError(f"Invalid JSON response from {url}: {e}")


def get_text(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    session: Optional[requests.Session] = None
) -> str:
    """Make a GET request and return text response.
    
    Args:
        url: URL to fetch.
        params: Query parameters.
        headers: Additional headers.
        timeout: Request timeout in seconds (uses config default if None).
        session: Requests session (uses global session if None).
        
    Returns:
        Response text.
        
    Raises:
        HttpError: If request fails.
        RateLimitError: If rate limit is hit (HTTP 429).
    """
    if session is None:
        session = get_session()
    
    if timeout is None:
        from npm.config import get_config
        timeout = get_config().request_timeout
    
    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        
        if response.status_code == 429:
            raise RateLimitError(
                f"Rate limit exceeded for {url}",
                status_code=429
            )
        
        response.raise_for_status()
        return response.text
    
    except requests.exceptions.Timeout as e:
        raise HttpError(f"Request timeout for {url}: {e}")
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        raise HttpError(f"Request failed for {url}: {e}", status_code=status_code)

