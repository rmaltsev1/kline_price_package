"""Utility helper functions."""

from datetime import datetime, timezone
from typing import Union, Optional


# =============================================================================
# Timeframe Normalization
# =============================================================================

# Universal timeframe format (Binance-style) -> Oanda format mapping
TIMEFRAME_TO_OANDA = {
    '1m': 'M1',
    '3m': 'M3',
    '5m': 'M5',
    '15m': 'M15',
    '30m': 'M30',
    '1h': 'H1',
    '2h': 'H2',
    '4h': 'H4',
    '6h': 'H6',
    '8h': 'H8',
    '12h': 'H12',
    '1d': 'D',
    '1w': 'W',
    '1M': 'M',
}

# Oanda format -> Universal timeframe format mapping
OANDA_TO_TIMEFRAME = {v: k for k, v in TIMEFRAME_TO_OANDA.items()}

# Valid universal timeframes (user-facing)
VALID_TIMEFRAMES = list(TIMEFRAME_TO_OANDA.keys())


def normalize_timeframe_to_oanda(timeframe: str) -> str:
    """
    Convert universal timeframe format to Oanda granularity.
    
    Args:
        timeframe: Universal timeframe (e.g., '1m', '1h', '1d')
        
    Returns:
        str: Oanda granularity (e.g., 'M1', 'H1', 'D')
        
    Raises:
        ValueError: If timeframe is not valid
    """
    if timeframe in TIMEFRAME_TO_OANDA:
        return TIMEFRAME_TO_OANDA[timeframe]
    
    # Check if already in Oanda format
    if timeframe in OANDA_TO_TIMEFRAME:
        return timeframe
    
    raise ValueError(f"Invalid timeframe '{timeframe}'. Valid options: {VALID_TIMEFRAMES}")


def normalize_timeframe_from_oanda(granularity: str) -> str:
    """
    Convert Oanda granularity to universal timeframe format.
    
    Args:
        granularity: Oanda granularity (e.g., 'M1', 'H1', 'D')
        
    Returns:
        str: Universal timeframe (e.g., '1m', '1h', '1d')
    """
    return OANDA_TO_TIMEFRAME.get(granularity, granularity)


# =============================================================================
# Symbol Normalization
# =============================================================================

def normalize_symbol_to_oanda(symbol: str) -> str:
    """
    Convert universal symbol format to Oanda instrument format.
    
    Handles both 6-char forex pairs and special symbols like XAU.
    
    Args:
        symbol: Universal symbol (e.g., 'EURUSD', 'XAUUSD')
        
    Returns:
        str: Oanda instrument (e.g., 'EUR_USD', 'XAU_USD')
    """
    # Already has underscore
    if "_" in symbol:
        return symbol
    
    # Standard 6-char forex pairs (e.g., EURUSD -> EUR_USD)
    if len(symbol) == 6:
        return f"{symbol[:3]}_{symbol[3:]}"
    
    # Handle 7-char symbols like XAUUSD -> XAU_USD
    if len(symbol) == 7:
        return f"{symbol[:3]}_{symbol[3:]}"
    
    return symbol


def normalize_symbol_from_oanda(instrument: str) -> str:
    """
    Convert Oanda instrument format to universal symbol format.
    
    Args:
        instrument: Oanda instrument (e.g., 'EUR_USD', 'XAU_USD')
        
    Returns:
        str: Universal symbol (e.g., 'EURUSD', 'XAUUSD')
    """
    return instrument.replace("_", "")


# =============================================================================
# Timestamp Helpers
# =============================================================================

def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """
    Convert Unix timestamp to datetime object.
    
    Args:
        timestamp: Unix timestamp in seconds or milliseconds
        
    Returns:
        datetime: Datetime object in UTC
    """
    # Handle both seconds and milliseconds
    if timestamp > 10**10:
        timestamp = timestamp / 1000
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime, milliseconds: bool = True) -> int:
    """
    Convert datetime to Unix timestamp.
    
    Args:
        dt: Datetime object
        milliseconds: Whether to return timestamp in milliseconds (default: True)
        
    Returns:
        int: Unix timestamp
    """
    timestamp = int(dt.timestamp())
    return timestamp * 1000 if milliseconds else timestamp


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_symbol(symbol: str) -> bool:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT', 'EURUSD')
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(symbol and len(symbol) >= 3)


def validate_timeframe(timeframe: str) -> bool:
    """
    Validate timeframe against universal format.
    
    Args:
        timeframe: Timeframe to validate (e.g., '1m', '1h', '1d')
        
    Returns:
        bool: True if valid, False otherwise
    """
    return timeframe in VALID_TIMEFRAMES


def validate_interval(interval: str, valid_intervals: list) -> bool:
    """
    Validate interval against list of valid intervals.
    
    Args:
        interval: Interval to validate
        valid_intervals: List of valid intervals
        
    Returns:
        bool: True if valid, False otherwise
    """
    return interval in valid_intervals
