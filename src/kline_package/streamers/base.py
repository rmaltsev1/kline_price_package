"""Base class for data streamers."""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Any
import asyncio


class BaseStreamer(ABC):
    """
    Abstract base class for all data streamers.
    
    All streamers should inherit from this class and implement
    the connect, disconnect, and subscribe methods.
    """
    
    def __init__(self):
        """Initialize the streamer."""
        self._running = False
        self._callbacks: dict = {}
    
    @property
    def is_running(self) -> bool:
        """Check if the streamer is currently running."""
        return self._running
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the streaming service.
        
        Raises:
            ConnectionError: If connection cannot be established
        """
        raise NotImplementedError("Subclasses must implement connect method")
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the connection to the streaming service.
        """
        raise NotImplementedError("Subclasses must implement disconnect method")
    
    @abstractmethod
    async def subscribe(self, symbol: str, callback: Callable[[dict], None], **kwargs) -> None:
        """
        Subscribe to a data stream for a symbol.
        
        Args:
            symbol: The trading symbol to subscribe to
            callback: Function to call when data is received
            **kwargs: Additional subscription parameters
        """
        raise NotImplementedError("Subclasses must implement subscribe method")
    
    @abstractmethod
    async def unsubscribe(self, symbol: str, **kwargs) -> None:
        """
        Unsubscribe from a data stream.
        
        Args:
            symbol: The trading symbol to unsubscribe from
            **kwargs: Additional parameters
        """
        raise NotImplementedError("Subclasses must implement unsubscribe method")
    
    def on_message(self, callback: Callable[[dict], None]) -> None:
        """
        Set a callback for all messages.
        
        Args:
            callback: Function to call when any message is received
        """
        self._callbacks['message'] = callback
    
    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """
        Set a callback for errors.
        
        Args:
            callback: Function to call when an error occurs
        """
        self._callbacks['error'] = callback
    
    def on_close(self, callback: Callable[[], None]) -> None:
        """
        Set a callback for connection close.
        
        Args:
            callback: Function to call when connection closes
        """
        self._callbacks['close'] = callback
    
    def _handle_error(self, error: Exception) -> None:
        """Handle errors by calling the error callback if set."""
        if 'error' in self._callbacks:
            self._callbacks['error'](error)
        else:
            print(f"Streamer error: {error}")
    
    def _handle_close(self) -> None:
        """Handle connection close by calling the close callback if set."""
        self._running = False
        if 'close' in self._callbacks:
            self._callbacks['close']()
