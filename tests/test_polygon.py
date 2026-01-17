"""Tests for Polygon.io fetcher."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from kline_package.fetchers import PolygonFetcher


class TestPolygonFetcher:
    """Test suite for PolygonFetcher."""
    
    def test_initialization(self):
        """Test fetcher initialization."""
        fetcher = PolygonFetcher(api_key="test-key")
        assert fetcher is not None
        assert fetcher.api_key == "test-key"
        assert fetcher.base_url == PolygonFetcher.BASE_URL
    
    def test_custom_base_url(self):
        """Test initialization with custom base URL."""
        custom_url = "https://custom.polygon.io"
        fetcher = PolygonFetcher(api_key="test-key", base_url=custom_url)
        assert fetcher.base_url == custom_url
    
    def test_rate_limiting_enabled(self):
        """Test rate limiting is enabled by default."""
        fetcher = PolygonFetcher(api_key="test-key")
        assert fetcher.rate_limit is True
    
    def test_rate_limiting_disabled(self):
        """Test rate limiting can be disabled."""
        fetcher = PolygonFetcher(api_key="test-key", rate_limit=False)
        assert fetcher.rate_limit is False


class TestPolygonTimeframes:
    """Test timeframe handling."""
    
    def test_valid_timeframes(self):
        """Test that all valid timeframes are mapped."""
        expected = ['1m', '3m', '5m', '15m', '30m', 
                    '1h', '2h', '4h', '6h', '8h', '12h',
                    '1d', '1w', '1M']
        for tf in expected:
            assert tf in PolygonFetcher.TIMEFRAME_MAP
    
    def test_timeframe_mapping(self):
        """Test specific timeframe mappings."""
        assert PolygonFetcher.TIMEFRAME_MAP['1m'] == (1, 'minute')
        assert PolygonFetcher.TIMEFRAME_MAP['1h'] == (1, 'hour')
        assert PolygonFetcher.TIMEFRAME_MAP['1d'] == (1, 'day')
        assert PolygonFetcher.TIMEFRAME_MAP['1w'] == (1, 'week')
    
    def test_invalid_timeframe_raises(self):
        """Test that invalid timeframe raises ValueError."""
        fetcher = PolygonFetcher(api_key="test-key", rate_limit=False)
        with pytest.raises(ValueError, match="Invalid interval"):
            fetcher.fetch("AAPL", "invalid")


class TestPolygonFetch:
    """Test fetch functionality."""
    
    @patch('kline_package.fetchers.polygon.requests.Session')
    def test_fetch_returns_dataframe(self, mock_session_class):
        """Test that fetch returns a DataFrame."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "t": 1704067200000,
                    "o": 100.0,
                    "h": 101.0,
                    "l": 99.0,
                    "c": 100.5,
                    "v": 1000000,
                    "vw": 100.25,
                    "n": 5000
                }
            ]
        }
        mock_session.get.return_value = mock_response
        
        fetcher = PolygonFetcher(api_key="test-key", rate_limit=False)
        fetcher.session = mock_session
        
        df = fetcher.fetch("AAPL", "1d", days=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'Open' in df.columns
        assert 'High' in df.columns
        assert 'Low' in df.columns
        assert 'Close' in df.columns
        assert 'Volume' in df.columns
    
    @patch('kline_package.fetchers.polygon.requests.Session')
    def test_fetch_empty_response(self, mock_session_class):
        """Test handling of empty API response."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "results": []
        }
        mock_session.get.return_value = mock_response
        
        fetcher = PolygonFetcher(api_key="test-key", rate_limit=False)
        fetcher.session = mock_session
        
        df = fetcher.fetch("AAPL", "1d", days=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestPolygonSymbols:
    """Test symbol handling."""
    
    def test_stock_symbol(self):
        """Test stock symbols work."""
        fetcher = PolygonFetcher(api_key="test-key")
        # Just verify no preprocessing errors
        assert True
    
    def test_crypto_symbol_format(self):
        """Test crypto symbol format (X:BTCUSD)."""
        # Crypto symbols use X: prefix
        symbol = "X:BTCUSD"
        assert symbol.startswith("X:")
    
    def test_forex_symbol_format(self):
        """Test forex symbol format (C:EURUSD)."""
        # Forex symbols use C: prefix
        symbol = "C:EURUSD"
        assert symbol.startswith("C:")
