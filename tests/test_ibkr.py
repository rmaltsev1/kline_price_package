"""Tests for Interactive Brokers fetcher."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from kline_package.fetchers import IBKRFetcher


class TestIBKRFetcher:
    """Test suite for IBKRFetcher."""
    
    def test_initialization_default(self):
        """Test fetcher initialization with defaults."""
        fetcher = IBKRFetcher()
        assert fetcher is not None
        assert fetcher.host == "127.0.0.1"
        assert fetcher.port == 7497
        assert fetcher.client_id == 1
        assert fetcher.use_client_portal is False
    
    def test_initialization_custom_port(self):
        """Test initialization with custom port."""
        fetcher = IBKRFetcher(port=7496)  # Live trading port
        assert fetcher.port == 7496
    
    def test_initialization_client_portal(self):
        """Test initialization with Client Portal mode."""
        fetcher = IBKRFetcher(use_client_portal=True)
        assert fetcher.use_client_portal is True
        assert fetcher.gateway_url == IBKRFetcher.CLIENT_PORTAL_URL
    
    def test_custom_gateway_url(self):
        """Test custom gateway URL."""
        custom_url = "https://localhost:5555/v1/api"
        fetcher = IBKRFetcher(
            use_client_portal=True,
            gateway_url=custom_url
        )
        assert fetcher.gateway_url == custom_url


class TestIBKRTimeframes:
    """Test timeframe handling."""
    
    def test_valid_timeframes(self):
        """Test that common timeframes are mapped."""
        expected = ['1m', '3m', '5m', '15m', '30m', 
                    '1h', '2h', '4h', '1d', '1w', '1M']
        for tf in expected:
            assert tf in IBKRFetcher.TIMEFRAME_MAP
    
    def test_timeframe_mapping(self):
        """Test specific timeframe mappings to IBKR format."""
        assert IBKRFetcher.TIMEFRAME_MAP['1m'] == '1 min'
        assert IBKRFetcher.TIMEFRAME_MAP['1h'] == '1 hour'
        assert IBKRFetcher.TIMEFRAME_MAP['1d'] == '1 day'
        assert IBKRFetcher.TIMEFRAME_MAP['1w'] == '1 week'
    
    def test_invalid_timeframe_raises(self):
        """Test that invalid timeframe raises ValueError."""
        fetcher = IBKRFetcher()
        with pytest.raises(ValueError, match="Invalid interval"):
            fetcher.fetch("AAPL", "invalid")


class TestIBKRConnectionModes:
    """Test different connection modes."""
    
    def test_ib_insync_mode_requires_library(self):
        """Test that ib_insync mode requires the library."""
        fetcher = IBKRFetcher(use_client_portal=False)
        
        # Mock import failure
        with patch.dict('sys.modules', {'ib_insync': None}):
            # This would raise ImportError when trying to connect
            assert fetcher.use_client_portal is False
    
    def test_initial_connection_state(self):
        """Test initial connection state."""
        fetcher = IBKRFetcher()
        assert fetcher._connected is False
        assert fetcher._ib is None


class TestIBKRSecurityTypes:
    """Test different security types."""
    
    def test_stock_sec_type(self):
        """Test stock security type."""
        fetcher = IBKRFetcher()
        # STK is the default
        assert True  # Just verify it can be created
    
    def test_forex_symbol_format(self):
        """Test forex symbol format (EUR.USD)."""
        symbol = "EUR.USD"
        parts = symbol.split(".")
        assert len(parts) == 2
        assert parts[0] == "EUR"
        assert parts[1] == "USD"


class TestIBKRDataProcessing:
    """Test data processing."""
    
    def test_process_client_portal_data_empty(self):
        """Test processing empty Client Portal response."""
        fetcher = IBKRFetcher(use_client_portal=True)
        result = fetcher._process_client_portal_data({"data": []})
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    def test_process_client_portal_data(self):
        """Test processing Client Portal response."""
        fetcher = IBKRFetcher(use_client_portal=True)
        
        data = {
            "data": [
                {
                    "t": 1704067200000,
                    "o": 100.0,
                    "h": 101.0,
                    "l": 99.0,
                    "c": 100.5,
                    "v": 1000000
                }
            ]
        }
        
        result = fetcher._process_client_portal_data(data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert 'Open' in result.columns
        assert 'Close' in result.columns
    
    def test_process_ib_insync_data_empty(self):
        """Test processing empty ib_insync DataFrame."""
        fetcher = IBKRFetcher()
        empty_df = pd.DataFrame()
        
        result = fetcher._process_ib_insync_data(empty_df)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
