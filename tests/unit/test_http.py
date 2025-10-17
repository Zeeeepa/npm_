"""Unit tests for HTTP utilities."""
import pytest
from unittest.mock import Mock, patch
import requests
from npm.utils.http import (
    create_session,
    get_session,
    reset_session,
    get_json,
    get_text,
    HttpError,
    RateLimitError,
)


class TestCreateSession:
    """Test create_session functionality."""
    
    def test_creates_session_with_defaults(self):
        """Test session creation with default parameters."""
        session = create_session()
        
        assert isinstance(session, requests.Session)
        assert "User-Agent" in session.headers
        assert "Mozilla" in session.headers["User-Agent"]
    
    def test_creates_session_with_custom_user_agent(self):
        """Test session creation with custom user agent."""
        custom_ua = "CustomBot/1.0"
        session = create_session(user_agent=custom_ua)
        
        assert session.headers["User-Agent"] == custom_ua
    
    def test_session_has_retry_adapter(self):
        """Test session has HTTPAdapter with retry logic."""
        session = create_session()
        
        # Check adapters are mounted
        assert session.get_adapter("http://") is not None
        assert session.get_adapter("https://") is not None


class TestGetSession:
    """Test get_session singleton functionality."""
    
    def test_get_session_returns_session(self, mock_env):
        """Test get_session returns a session instance."""
        reset_session()  # Clear any existing session
        session = get_session()
        
        assert isinstance(session, requests.Session)
    
    def test_get_session_returns_singleton(self, mock_env):
        """Test get_session returns same instance on multiple calls."""
        reset_session()
        session1 = get_session()
        session2 = get_session()
        
        assert session1 is session2
    
    def test_reset_session_clears_singleton(self, mock_env):
        """Test reset_session clears the cached session."""
        session1 = get_session()
        reset_session()
        session2 = get_session()
        
        assert session1 is not session2


class TestGetJson:
    """Test get_json functionality."""
    
    @patch('npm.utils.http.get_session')
    def test_get_json_success(self, mock_get_session, mock_response):
        """Test successful JSON retrieval."""
        test_data = {"key": "value", "number": 42}
        mock_session = Mock()
        mock_session.get.return_value = mock_response(json_data=test_data)
        mock_get_session.return_value = mock_session
        
        result = get_json("https://example.com/api")
        
        assert result == test_data
        mock_session.get.assert_called_once()
    
    @patch('npm.utils.http.get_session')
    def test_get_json_with_params(self, mock_get_session, mock_response):
        """Test get_json with query parameters."""
        mock_session = Mock()
        mock_session.get.return_value = mock_response(json_data={"test": "data"})
        mock_get_session.return_value = mock_session
        
        params = {"page": 1, "limit": 10}
        get_json("https://example.com/api", params=params)
        
        mock_session.get.assert_called_with(
            "https://example.com/api",
            params=params,
            headers=None,
            timeout=30  # Default from config
        )
    
    @patch('npm.utils.http.get_session')
    def test_get_json_rate_limit_error(self, mock_get_session, mock_response):
        """Test get_json raises RateLimitError on HTTP 429."""
        mock_session = Mock()
        mock_session.get.return_value = mock_response(status_code=429)
        mock_get_session.return_value = mock_session
        
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            get_json("https://example.com/api")
    
    @patch('npm.utils.http.get_session')
    def test_get_json_http_error(self, mock_get_session, mock_response):
        """Test get_json raises HttpError on HTTP errors."""
        mock_session = Mock()
        response = mock_response(status_code=500)
        mock_session.get.return_value = response
        mock_get_session.return_value = mock_session
        
        with pytest.raises(HttpError):
            get_json("https://example.com/api")
    
    @patch('npm.utils.http.get_session')
    def test_get_json_timeout_error(self, mock_get_session):
        """Test get_json raises HttpError on timeout."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.Timeout("Connection timeout")
        mock_get_session.return_value = mock_session
        
        with pytest.raises(HttpError, match="timeout"):
            get_json("https://example.com/api")
    
    @patch('npm.utils.http.get_session')
    def test_get_json_invalid_json(self, mock_get_session):
        """Test get_json raises HttpError on invalid JSON."""
        mock_session = Mock()
        response = Mock()
        response.status_code = 200
        response.json.side_effect = ValueError("Invalid JSON")
        response.raise_for_status = Mock()
        mock_session.get.return_value = response
        mock_get_session.return_value = mock_session
        
        with pytest.raises(HttpError, match="Invalid JSON"):
            get_json("https://example.com/api")


class TestGetText:
    """Test get_text functionality."""
    
    @patch('npm.utils.http.get_session')
    def test_get_text_success(self, mock_get_session, mock_response):
        """Test successful text retrieval."""
        test_text = "<html>Hello World</html>"
        mock_session = Mock()
        mock_session.get.return_value = mock_response(text=test_text)
        mock_get_session.return_value = mock_session
        
        result = get_text("https://example.com/page")
        
        assert result == test_text
        mock_session.get.assert_called_once()
    
    @patch('npm.utils.http.get_session')
    def test_get_text_rate_limit_error(self, mock_get_session, mock_response):
        """Test get_text raises RateLimitError on HTTP 429."""
        mock_session = Mock()
        mock_session.get.return_value = mock_response(status_code=429)
        mock_get_session.return_value = mock_session
        
        with pytest.raises(RateLimitError):
            get_text("https://example.com/page")
    
    @patch('npm.utils.http.get_session')
    def test_get_text_with_custom_session(self, mock_get_session, mock_response):
        """Test get_text with custom session."""
        custom_session = Mock()
        custom_session.get.return_value = mock_response(text="custom")
        
        result = get_text("https://example.com/page", session=custom_session)
        
        assert result == "custom"
        custom_session.get.assert_called_once()
        mock_get_session.assert_not_called()  # Should not call global session


class TestHttpErrors:
    """Test HTTP error classes."""
    
    def test_http_error_with_status_code(self):
        """Test HttpError stores status code."""
        error = HttpError("Test error", status_code=404)
        
        assert str(error) == "Test error"
        assert error.status_code == 404
    
    def test_http_error_without_status_code(self):
        """Test HttpError works without status code."""
        error = HttpError("Test error")
        
        assert str(error) == "Test error"
        assert error.status_code is None
    
    def test_rate_limit_error_inherits_http_error(self):
        """Test RateLimitError is subclass of HttpError."""
        error = RateLimitError("Rate limited", status_code=429)
        
        assert isinstance(error, HttpError)
        assert error.status_code == 429

