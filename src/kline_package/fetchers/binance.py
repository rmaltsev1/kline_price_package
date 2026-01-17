"""Binance data fetcher using direct API integration."""

from typing import Optional, List
import pandas as pd
import requests
from datetime import datetime, timezone

from kline_package.fetchers.base import BaseFetcher
from kline_package.utils.helpers import VALID_TIMEFRAMES


class BinanceFetcher(BaseFetcher):
    """
    Fetcher for Binance cryptocurrency exchange data.
    
    This class fetches kline/candlestick data directly from Binance API
    without requiring any API keys for public endpoints.
    """
    
    BASE_URL = "https://api.binance.com/api/v3/klines"
    VALID_INTERVALS = VALID_TIMEFRAMES  # Universal timeframe format
    
    def __init__(self, base_url: Optional[str] = None, valid_symbols: Optional[List[str]] = None):
        """
        Initialize the Binance fetcher.
        
        Args:
            base_url: Optional custom base URL (default: Binance public API)
            valid_symbols: Optional list of valid symbols to restrict to
        """
        super().__init__()
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self.valid_symbols = valid_symbols
    
    def fetch(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch kline/candlestick data from Binance.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '1m', '5m', '1h', '1d')
                     Valid intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
            limit: Number of klines to fetch (max 1000, default 500)
            start_time: Start time in milliseconds (optional)
            end_time: End time in milliseconds (optional)
            
        Returns:
            pd.DataFrame: DataFrame with columns:
                - Open Time: Opening time (datetime)
                - Open: Open price
                - High: High price
                - Low: Low price
                - Close: Close price
                - Volume: Trading volume
                - Close Time: Closing time
                - Quote asset volume: Quote asset volume
                - Number of trades: Number of trades
                - Taker buy base asset volume: Taker buy base asset volume
                - Taker buy quote asset volume: Taker buy quote asset volume
                - Ignore: Ignore field
                
        Raises:
            requests.exceptions.RequestException: If API request fails
            ValueError: If parameters are invalid
        """
        # Validate interval
        if interval not in self.VALID_INTERVALS:
            raise ValueError(f"Invalid interval. Valid options: {self.VALID_INTERVALS}")
        
        # Validate symbol if valid_symbols is set
        if self.valid_symbols and symbol not in self.valid_symbols:
            raise ValueError(f"Invalid symbol. Valid options: {self.valid_symbols}")
        
        # If both start and end time provided, fetch all data in batches
        if start_time and end_time:
            return self._fetch_all_data(symbol, interval, start_time, end_time)
        
        # Single request
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': min(limit, 1000)  # Binance max is 1000
        }
        
        if start_time:
            params['startTime'] = start_time
        
        if end_time:
            params['endTime'] = end_time
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._process_kline_data(data)
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch data from Binance: {e}")
        except Exception as e:
            raise Exception(f"Error processing Binance data: {e}")
    
    def _fetch_all_data(self, symbol: str, interval: str, start_time: int, end_time: int) -> pd.DataFrame:
        """
        Fetch all data between start and end times in chunks of 1000.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            pd.DataFrame: Combined DataFrame with all data
        """
        all_data = []
        current_start = start_time
        
        while True:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': 1000,
                'startTime': current_start,
                'endTime': end_time
            }
            
            try:
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                all_data.extend(data)
                
                # Get the last timestamp and check if we've reached the end
                last_timestamp = data[-1][0]
                if last_timestamp >= end_time or len(data) < 1000:
                    break
                
                # Update current_start for next iteration (add 1ms to avoid duplicate)
                current_start = last_timestamp + 1
            
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to fetch data from Binance: {e}")
        
        return self._process_kline_data(all_data)
    
    def _process_kline_data(self, data: list) -> pd.DataFrame:
        """
        Process raw kline data into DataFrame.
        
        Args:
            data: Raw kline data from API
            
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        df = pd.DataFrame(data, columns=[
            'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time',
            'Quote asset volume', 'Number of trades', 'Taker buy base asset volume',
            'Taker buy quote asset volume', 'Ignore'
        ])
        
        df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms', utc=True)
        df['Open'] = df['Open'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Close'] = df['Close'].astype(float)
        df['Volume'] = df['Volume'].astype(float)
        
        return df.reset_index(drop=True)
