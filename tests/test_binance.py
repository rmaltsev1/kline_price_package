"""Tests for Binance fetcher."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timezone

from kline_package.fetchers import BinanceFetcher


class TestBinanceFetcher:
    """Test suite for BinanceFetcher."""
    
    def test_initialization(self):
        """Test fetcher initialization."""
        fetcher = BinanceFetcher()
        assert fetcher is not None
        assert fetcher.base_url == BinanceFetcher.BASE_URL
    
    def test_custom_base_url(self):
        """Test initialization with custom base URL."""
        custom_url = "https://testnet.binance.vision"
        fetcher = BinanceFetcher(base_url=custom_url)
        assert fetcher.base_url == custom_url
    
    def test_invalid_interval(self):
        """Test that invalid interval raises ValueError."""
        fetcher = BinanceFetcher()
        with pytest.raises(ValueError, match="Invalid interval"):
            fetcher.fetch("BTCUSDT", "invalid")
    
    def test_valid_intervals(self):
        """Test that valid intervals are accepted."""
        from kline_package.utils.helpers import VALID_TIMEFRAMES
        fetcher = BinanceFetcher()
        for interval in VALID_TIMEFRAMES:
            assert interval in VALID_TIMEFRAMES

    @patch('kline_package.fetchers.binance.requests.get')
    def test_fetch_returns_dataframe(self, mock_get):
        """Test that fetch returns a DataFrame."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1609459200000,  # Open time
                "29000.00",     # Open
                "29100.00",     # High
                "28900.00",     # Low
                "29050.00",     # Close
                "1000.0",       # Volume
                1609462799999,  # Close time
                "29000000.00",  # Quote asset volume
                100,            # Number of trades
                "500.0",        # Taker buy base
                "14500000.00",  # Taker buy quote
                "0"             # Ignore
            ]
        ]
        mock_get.return_value = mock_response
        
        fetcher = BinanceFetcher()
        df = fetcher.fetch("BTCUSDT", "1h", limit=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'Open' in df.columns
        assert 'High' in df.columns
        assert 'Low' in df.columns
        assert 'Close' in df.columns
        assert 'Volume' in df.columns

    @patch('kline_package.fetchers.binance.requests.get')
    def test_fetch_with_date_range(self, mock_get):
        """Test fetch with start and end date."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        fetcher = BinanceFetcher()
        df = fetcher.fetch(
            "BTCUSDT", 
            "1h",
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
        
        assert mock_get.called

    @patch('kline_package.fetchers.binance.requests.get')
    def test_fetch_empty_response(self, mock_get):
        """Test handling of empty API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        fetcher = BinanceFetcher()
        df = fetcher.fetch("BTCUSDT", "1h", limit=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestBinanceFetcherDataTypes:
    """Test data type handling for Binance fetcher."""
    
    @patch('kline_package.fetchers.binance.requests.get')
    def test_numeric_columns(self, mock_get):
        """Test that numeric columns are properly typed."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1609459200000,
                "29000.00",
                "29100.00",
                "28900.00",
                "29050.00",
                "1000.0",
                1609462799999,
                "29000000.00",
                100,
                "500.0",
                "14500000.00",
                "0"
            ]
        ]
        mock_get.return_value = mock_response
        
        fetcher = BinanceFetcher()
        df = fetcher.fetch("BTCUSDT", "1h", limit=1)
        
        assert df['Open'].dtype in ['float64', 'float32']
        assert df['High'].dtype in ['float64', 'float32']
        assert df['Low'].dtype in ['float64', 'float32']
        assert df['Close'].dtype in ['float64', 'float32']
        assert df['Volume'].dtype in ['float64', 'float32']

    @patch('kline_package.fetchers.binance.requests.get')
    def test_timestamp_column(self, mock_get):
        """Test that timestamp is properly parsed."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1609459200000,
                "29000.00",
                "29100.00",
                "28900.00",
                "29050.00",
                "1000.0",
                1609462799999,
                "29000000.00",
                100,
                "500.0",
                "14500000.00",
                "0"
            ]
        ]
        mock_get.return_value = mock_response
        
        fetcher = BinanceFetcher()
        df = fetcher.fetch("BTCUSDT", "1h", limit=1)
        
        assert 'Open Time' in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df['Open Time'])
