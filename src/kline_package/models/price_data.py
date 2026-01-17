"""Price data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PriceData:
    """
    Data class for price/candle data.
    
    This provides a common structure for price data from different sources.
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str  # 'binance' or 'oanda'
    symbol: str  # Trading pair or instrument
    
    # Optional fields
    close_time: Optional[datetime] = None
    quote_volume: Optional[float] = None
    trades: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'source': self.source,
            'symbol': self.symbol,
            'close_time': self.close_time,
            'quote_volume': self.quote_volume,
            'trades': self.trades,
        }
