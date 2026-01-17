"""Base class for data fetchers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd


class BaseFetcher(ABC):
    """
    Abstract base class for all data fetchers.
    
    All fetchers should inherit from this class and implement the fetch method.
    """
    
    def __init__(self):
        """Initialize the fetcher."""
        pass
    
    @abstractmethod
    def fetch(self, **kwargs) -> pd.DataFrame:
        """
        Fetch data from the source.
        
        Args:
            **kwargs: Implementation-specific parameters
            
        Returns:
            pd.DataFrame: A pandas DataFrame containing the fetched data
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement fetch method")
    
    def _validate_response(self, response: Any) -> bool:
        """
        Validate the API response.
        
        Args:
            response: The response object to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return True
    
    def _handle_error(self, error: Exception) -> None:
        """
        Handle errors during data fetching.
        
        Args:
            error: The exception that occurred
            
        Raises:
            Exception: Re-raises the exception after logging
        """
        print(f"Error in {self.__class__.__name__}: {str(error)}")
        raise error
