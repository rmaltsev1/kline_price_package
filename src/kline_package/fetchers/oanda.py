"""Oanda data fetcher using direct API integration."""

from typing import Optional, List
import pandas as pd
import requests
from datetime import datetime

from kline_package.fetchers.base import BaseFetcher
from kline_package.utils.helpers import (
    normalize_symbol_to_oanda,
    normalize_timeframe_to_oanda,
    VALID_TIMEFRAMES,
)


class OandaFetcher(BaseFetcher):
    """
    Fetcher for Oanda forex and CFD data.
    
    This class fetches candle data from Oanda API.
    Requires API key and account ID for authentication.
    """
    
    # Oanda has different URLs for practice and live accounts
    PRACTICE_URL = "https://api-fxpractice.oanda.com"
    LIVE_URL = "https://api-fxtrade.oanda.com"
    VALID_GRANULARITIES = ['S5', 'S10', 'S15', 'S30', 'M1', 'M2', 'M4', 'M5', 'M10', 'M15', 'M30',
                           'H1', 'H2', 'H3', 'H4', 'H6', 'H8', 'H12', 'D', 'W', 'M']
    
    def __init__(
        self,
        api_key: str,
        account_id: str,
        practice: bool = True,
        base_url: Optional[str] = None,
        valid_instruments: Optional[List[str]] = None
    ):
        """
        Initialize the Oanda fetcher.
        
        Args:
            api_key: Oanda API key
            account_id: Oanda account ID
            practice: Whether to use practice account (default: True)
            base_url: Optional custom base URL
            valid_instruments: Optional list of valid instruments to restrict to
        """
        super().__init__()
        self.api_key = api_key
        self.account_id = account_id
        self.valid_instruments = valid_instruments
        
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = self.PRACTICE_URL if practice else self.LIVE_URL
        
        self.base_instruments_url = f"{self.base_url}/v3/accounts/{account_id}/instruments"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept-Datetime-Format': 'RFC3339',
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'accountID': account_id,
        })
    
    def fetch(
        self,
        symbol: str,
        interval: str = "1h",
        count: int = 500,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        price: str = "M"
    ) -> pd.DataFrame:
        """
        Fetch candle data from Oanda.
        
        Args:
            symbol: Symbol name in universal format (e.g., 'EURUSD', 'GBPUSD', 'XAUUSD')
                   Will be automatically converted to Oanda format (e.g., 'EUR_USD')
            interval: Candle interval in universal format (e.g., '1m', '5m', '1h', '1d')
                     Valid: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w, 1M
            count: Number of candles to fetch (max 5000, default 500)
            from_time: Start time in RFC3339 format (optional)
            to_time: End time in RFC3339 format (optional)
            price: Price component ('M' for midpoint, 'B' for bid, 'A' for ask)
            
        Returns:
            pd.DataFrame: DataFrame with columns:
                - Open Time: Candle timestamp (datetime)
                - Open: Open price
                - High: High price
                - Low: Low price
                - Close: Close price
                - Volume: Trading volume
                
        Raises:
            requests.exceptions.RequestException: If API request fails
            ValueError: If parameters are invalid or authentication fails
        """
        # Normalize symbol to Oanda format (EURUSD -> EUR_USD)
        instrument = normalize_symbol_to_oanda(symbol)
        
        # Normalize timeframe to Oanda granularity (1h -> H1)
        granularity = normalize_timeframe_to_oanda(interval)
        
        # Validate instrument if valid_instruments is set
        if self.valid_instruments:
            # Normalize valid_instruments for comparison
            normalized_valid = [normalize_symbol_to_oanda(s) for s in self.valid_instruments]
            if instrument not in normalized_valid:
                raise ValueError(f"Invalid symbol. Valid options: {self.valid_instruments}")
        
        # If both from_time and to_time are provided, use batch fetching
        if from_time and to_time:
            return self._fetch_all_data_batched(instrument, granularity, from_time, to_time, price)
        
        # Single request for no date range or partial range
        return self._fetch_single_request(instrument, granularity, count, from_time, to_time, price)
    
    def _fetch_single_request(
        self, 
        instrument: str, 
        granularity: str, 
        count: int,
        from_time: Optional[str], 
        to_time: Optional[str],
        price: str
    ) -> pd.DataFrame:
        """
        Fetch data with a single API request.
        
        Args:
            instrument: Instrument name
            granularity: Candle granularity
            count: Number of candles to fetch
            from_time: Start time (optional)
            to_time: End time (optional)
            price: Price component
            
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        url = f"{self.base_instruments_url}/{instrument}/candles"
        
        params = {
            'granularity': granularity,
            'count': min(count, 5000),  # Maximum allowed by OANDA
            'price': price
        }
        
        if from_time:
            params['from'] = from_time
        
        if to_time:
            params['to'] = to_time
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'candles' not in data:
                raise Exception("No candle data returned from Oanda API")
            
            return self._process_candle_data(data['candles'], price)
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch data from Oanda: {e}")
        except Exception as e:
            raise Exception(f"Error processing Oanda data: {e}")
    
    def _fetch_all_data_batched(
        self, 
        instrument: str, 
        granularity: str, 
        from_time: str, 
        to_time: str,
        price: str = "M"
    ) -> pd.DataFrame:
        """
        Fetch all data between start and end dates in batches of 5000 candles.
        
        Args:
            instrument: Instrument name
            granularity: Candle granularity
            from_time: Start time in RFC3339 format
            to_time: End time in RFC3339 format
            price: Price component
            
        Returns:
            pd.DataFrame: Combined DataFrame with all data
        """
        all_candles = []
        current_start = from_time
        end_dt = pd.to_datetime(to_time, utc=True)
        
        batch_count = 0
        
        while True:
            batch_count += 1
            
            url = f"{self.base_instruments_url}/{instrument}/candles"
            params = {
                'granularity': granularity,
                'from': current_start,
                'count': 5000,  # Use count instead of 'to' for batching
                'price': price
            }
            
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'candles' not in data or not data['candles']:
                    break
                
                batch_candles = data['candles']
                complete_candles = [c for c in batch_candles if c['complete']]
                
                if not complete_candles:
                    break
                
                all_candles.extend(complete_candles)
                
                # Get the last candle's timestamp
                last_candle_time = pd.to_datetime(complete_candles[-1]['time'], utc=True)
                
                # Check if we've reached or passed the end date
                if last_candle_time >= end_dt or len(complete_candles) < 5000:
                    break
                
                # Set the next start time to be 1 minute after the last candle
                next_start = last_candle_time + pd.Timedelta(minutes=1)
                current_start = next_start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to fetch data from Oanda: {e}")
        
        return self._process_candle_data(all_candles, price)
    
    def _process_candle_data(self, candles: list, price_type: str = "M") -> pd.DataFrame:
        """
        Process raw candle data into DataFrame.
        
        Args:
            candles: Raw candle data from API
            price_type: Price type used ('M', 'B', or 'A')
            
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        processed_candles = []
        
        # Determine which price field to use
        price_field = price_type.lower()
        if price_field not in ['mid', 'bid', 'ask']:
            if price_type == 'M':
                price_field = 'mid'
            elif price_type == 'B':
                price_field = 'bid'
            elif price_type == 'A':
                price_field = 'ask'
        
        for candle in candles:
            if candle.get('complete', True):  # Only process complete candles
                processed_candles.append({
                    'Open Time': candle['time'],
                    'Open': float(candle[price_field]['o']),
                    'High': float(candle[price_field]['h']),
                    'Low': float(candle[price_field]['l']),
                    'Close': float(candle[price_field]['c']),
                    'Volume': int(candle['volume'])
                })
        
        df = pd.DataFrame(processed_candles)
        
        if not df.empty:
            df['Open Time'] = pd.to_datetime(df['Open Time'], utc=True)
            # Remove any duplicate timestamps
            df = df.drop_duplicates(subset=['Open Time']).reset_index(drop=True)
            df = df.sort_values('Open Time').reset_index(drop=True)
        
        return df
    
    def get_instruments(self) -> list:
        """
        Get list of available instruments.
        
        Returns:
            list: List of available instrument names
        """
        url = f"{self.base_url}/v3/accounts/{self.account_id}/instruments"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'instruments' in data:
                return [inst['name'] for inst in data['instruments']]
            return []
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch instruments from Oanda: {e}")
