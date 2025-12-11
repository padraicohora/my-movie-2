"""
TMDB API Client with Netskope SSL certificate support.

This module provides a configured requests session that handles
SSL certificate verification for environments using Netskope SSL inspection.
"""

import os
import certifi
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class TMDBClient:
    """
    HTTP client for TMDB API with proper SSL certificate configuration.
    
    This client automatically handles the Netskope certificate setup by:
    1. Unsetting REQUESTS_CA_BUNDLE environment variable
    2. Using the certifi bundle (which includes Netskope certificates)
    """
    
    def __init__(self):
        """
        Initialize the TMDB client.
        
        Args:
            api_key: TMDB API key (Bearer token)
        """
        self.api_key = os.getenv("TMDB_API_KEY")
        if not self.api_key:
            raise RuntimeError("TMDB_API_KEY not found in .env")
        self.base_url = "https://api.themoviedb.org/3"

        
        # Unset REQUESTS_CA_BUNDLE to use certifi bundle instead
        # The certifi bundle has been replaced with the Netskope combined bundle
        if "REQUESTS_CA_BUNDLE" in os.environ:
            del os.environ["REQUESTS_CA_BUNDLE"]
        
        # Get the certifi bundle path (contains Netskope certificates)
        self.cert_bundle = certifi.where()
        
        # Create a session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        })
        # Set the certificate bundle for all requests
        self.session.verify = self.cert_bundle
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a GET request to the TMDB API.
        
        Args:
            endpoint: API endpoint (e.g., "/movie/550" or "movie/550")
            params: Optional query parameters
            
        Returns:
            Response object
            
        Example:
            >>> client = TMDBClient(api_key="your_key")
            >>> response = client.get("/movie/550")
            >>> data = response.json()
        """
        url = self._build_url(endpoint)
        return self.session.get(url, params=params)
    
    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, 
             data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a POST request to the TMDB API.
        
        Args:
            endpoint: API endpoint
            json: Optional JSON data to send
            data: Optional form data to send
            
        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self.session.post(url, json=json, data=data)
    
    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a PUT request to the TMDB API.
        
        Args:
            endpoint: API endpoint
            json: Optional JSON data to send
            
        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self.session.put(url, json=json)
    
    def delete(self, endpoint: str) -> requests.Response:
        """
        Make a DELETE request to the TMDB API.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self.session.delete(url)
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build the full URL from an endpoint.
        
        Args:
            endpoint: API endpoint (with or without leading slash)
            
        Returns:
            Full URL
        """
        # Remove leading slash if present
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}"
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for one-off requests
def make_tmdb_request(
    endpoint: str,
    method: str = "GET",
    **kwargs
) -> requests.Response:
    """
    Make a one-off request to the TMDB API with proper SSL configuration.
    
    Args:
        endpoint: API endpoint

        method: HTTP method (GET, POST, PUT, DELETE)
        **kwargs: Additional arguments to pass to requests
        
    Returns:
        Response object
        
    Example:
        >>> response = make_tmdb_request("/movie/550", api_key="your_key")
        >>> data = response.json()
    """
    with TMDBClient() as client:
        method = method.upper()
        if method == "GET":
            return client.get(endpoint, params=kwargs.get('params'))
        elif method == "POST":
            return client.post(endpoint, json=kwargs.get('json'), data=kwargs.get('data'))
        elif method == "PUT":
            return client.put(endpoint, json=kwargs.get('json'))
        elif method == "DELETE":
            return client.delete(endpoint)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
