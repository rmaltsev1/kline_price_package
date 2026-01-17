"""Polygon.io fetcher for stocks, forex, and crypto data."""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import requests
import pandas as pd

from kline_package.fetchers.base import BaseFetcher
from kline_package.utils.helpers import VALID_TIMEFRAMES


class PolygonFetcher(BaseFetcher):
    """
    Fetcher for Polygon.io market data API.
    
    Supports stocks, forex, and crypto data.
    Free tier: 5 API calls/minute, delayed data, last 2 years.
    
    Example:
        ```python
        from kline_package import PolygonFetcher
        
        # Initialize with API key
        fetcher = PolygonFetcher(api_key="your-api-key")
        
        # Fetch stock data
        df = fetcher.fetch("AAPL", "1d", start_date="2024-01-01")
        
        # Fetch crypto data
        df = fetcher.fetch("X:BTCUSD", "1h", days=7)
        
        # Fetch forex data
        df = fetcher.fetch("C:EURUSD", "1h", days=7)
        ```
    
    Symbol formats:
        - Stocks: "AAPL", "MSFT", "GOOGL"
        - Crypto: "X:BTCUSD", "X:ETHUSD"
        - Forex: "C:EURUSD", "C:GBPUSD"
    """
    
    BASE_URL = "https://api.polygon.io"
    
    # Map universal timeframes to Polygon format (multiplier, timespan)
    TIMEFRAME_MAP = {
        '1m': (1, 'minute'),
        '3m': (3, 'minute'),
        '5m': (5, 'minute'),
        '15m': (15, 'minute'),
        '30m': (30, 'minute'),
        '1h': (1, 'hour'),
        '2h': (2, 'hour'),
        '4h': (4, 'hour'),
        '6h': (6, 'hour'),
        '8h': (8, 'hour'),
        '12h': (12, 'hour'),
        '1d': (1, 'day'),
        '1w': (1, 'week'),
        '1M': (1, 'month'),
    }
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        rate_limit: bool = True
    ):
        """
        Initialize the Polygon fetcher.
        
        Args:
            api_key: Polygon.io API key
            base_url: Optional custom API URL
            rate_limit: Whether to respect rate limits (default: True)
        """
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.rate_limit = rate_limit
        self._last_request_time = 0
        self._min_request_interval = 12.5  # 5 calls/min for free tier = 12 seconds
        
        self.session = requests.Session()
    
    def _wait_for_rate_limit(self) -> None:
        """Wait to respect rate limits."""
        if not self.rate_limit:
            return
        
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def fetch(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        days: Optional[int] = None,
        limit: int = 50000,
        adjusted: bool = True
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Polygon.io.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'X:BTCUSD', 'C:EURUSD')
            interval: Timeframe (e.g., '1m', '1h', '1d')
            start_date: Start date (string 'YYYY-MM-DD' or datetime)
            end_date: End date (string 'YYYY-MM-DD' or datetime)
            days: Alternative to start_date - fetch last N days
            limit: Maximum number of results (default: 50000)
            adjusted: Whether to adjust for splits (default: True)
            
        Returns:
            pd.DataFrame: OHLCV data with columns:
                - Open Time: Timestamp (datetime)
                - Open, High, Low, Close: Prices
                - Volume: Trading volume
                - VWAP: Volume-weighted average price
                - Trades: Number of trades
        """
        # Validate interval
        if interval not in self.TIMEFRAME_MAP:
            raise ValueError(f"Invalid interval '{interval}'. Valid: {list(self.TIMEFRAME_MAP.keys())}")
        
        multiplier, timespan = self.TIMEFRAME_MAP[interval]
        
        # Handle dates
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        
        if start_date is None:
            if days:
                start_date = end_date - timedelta(days=days)
            else:
                start_date = end_date - timedelta(days=30)
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        
        # Format dates for API
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Build URL
        url = (
            f"{self.base_url}/v2/aggs/ticker/{symbol}/range/"
            f"{multiplier}/{timespan}/{from_date}/{to_date}"
        )
        
        params = {
            "apiKey": self.api_key,
            "limit": limit,
            "adjusted": str(adjusted).lower(),
            "sort": "asc"
        }
        
        all_data = []
        
        while True:
            self._wait_for_rate_limit()
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 429:
                # Rate limited - wait and retry
                time.sleep(60)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "ERROR":
                raise ValueError(f"Polygon API error: {data.get('error', 'Unknown error')}")
            
            results = data.get("results", [])
            if not results:
                break
            
            all_data.extend(results)
            
            # Check for pagination
            next_url = data.get("next_url")
            if next_url:
                url = next_url
                params = {"apiKey": self.api_key}
            else:
                break
        
        if not all_data:
            return pd.DataFrame()
        
        return self._process_data(all_data)
    
    def _process_data(self, data: list) -> pd.DataFrame:
        """Process raw API data into DataFrame."""
        df = pd.DataFrame(data)
        
        # Rename columns
        column_map = {
            't': 'Open Time',
            'o': 'Open',
            'h': 'High',
            'l': 'Low',
            'c': 'Close',
            'v': 'Volume',
            'vw': 'VWAP',
            'n': 'Trades'
        }
        
        df = df.rename(columns=column_map)
        
        # Convert timestamp
        df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms', utc=True)
        
        # Ensure numeric types
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Select and order columns
        output_cols = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        if 'VWAP' in df.columns:
            output_cols.append('VWAP')
        if 'Trades' in df.columns:
            output_cols.append('Trades')
        
        return df[output_cols].reset_index(drop=True)
    
    def get_ticker_details(self, symbol: str) -> dict:
        """
        Get details about a ticker.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            dict: Ticker details including name, market, type, etc.
        """
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}/v3/reference/tickers/{symbol}"
        params = {"apiKey": self.api_key}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get("results", {})
    
    def search_tickers(
        self,
        query: str,
        market: str = "stocks",
        limit: int = 10
    ) -> list:
        """
        Search for tickers.
        
        Args:
            query: Search query
            market: Market type ('stocks', 'crypto', 'fx')
            limit: Maximum results
            
        Returns:
            list: Matching tickers
        """
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}/v3/reference/tickers"
        params = {
            "apiKey": self.api_key,
            "search": query,
            "market": market,
            "limit": limit,
            "active": "true"
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get("results", [])
