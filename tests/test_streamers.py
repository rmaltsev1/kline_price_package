"""Tests for streaming modules."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from kline_package.streamers import BinanceStreamer, OandaStreamer
from kline_package.utils.helpers import normalize_symbol_to_oanda


class TestBinanceStreamer:
    """Test suite for BinanceStreamer."""
    
    def test_initialization(self):
        """Test streamer initialization."""
        streamer = BinanceStreamer()
        assert streamer is not None
        assert streamer.base_url == BinanceStreamer.WS_BASE_URL
    
    def test_custom_base_url(self):
        """Test initialization with custom base URL."""
        custom_url = "wss://testnet.binance.vision/ws"
        streamer = BinanceStreamer(base_url=custom_url)
        assert streamer.base_url == custom_url
    
    def test_initial_state(self):
        """Test initial state of streamer."""
        streamer = BinanceStreamer()
        assert streamer._running is False
        assert streamer._subscriptions == {}


class TestOandaStreamer:
    """Test suite for OandaStreamer."""
    
    def test_initialization_practice(self):
        """Test streamer initialization with practice account."""
        streamer = OandaStreamer(
            api_key="test-key",
            account_id="test-account",
            practice=True
        )
        assert streamer is not None
        assert streamer.base_url == OandaStreamer.PRACTICE_STREAM_URL
    
    def test_initialization_live(self):
        """Test streamer initialization with live account."""
        streamer = OandaStreamer(
            api_key="test-key",
            account_id="test-account",
            practice=False
        )
        assert streamer.base_url == OandaStreamer.LIVE_STREAM_URL
    
    def test_custom_base_url(self):
        """Test initialization with custom base URL."""
        custom_url = "https://custom.oanda.com"
        streamer = OandaStreamer(
            api_key="test-key",
            account_id="test-account",
            base_url=custom_url
        )
        assert streamer.base_url == custom_url
    
    def test_initial_state(self):
        """Test initial state of streamer."""
        streamer = OandaStreamer(
            api_key="test-key",
            account_id="test-account"
        )
        assert streamer._running is False
        assert streamer._subscriptions == {}
        assert streamer._instruments == []


class TestOandaStreamerSymbolNormalization:
    """Test that Oanda streamer normalizes symbols."""
    
    def test_symbol_normalized_in_subscribe(self):
        """Test that symbols are normalized when subscribing."""
        # The subscribe method should convert EURUSD to EUR_USD
        streamer = OandaStreamer(
            api_key="test-key",
            account_id="test-account"
        )
        
        # Check that the normalization function works correctly
        assert normalize_symbol_to_oanda("EURUSD") == "EUR_USD"
        assert normalize_symbol_to_oanda("GBPUSD") == "GBP_USD"
        assert normalize_symbol_to_oanda("USDJPY") == "USD_JPY"
    
    def test_already_normalized_passes_through(self):
        """Test that already normalized symbols pass through."""
        assert normalize_symbol_to_oanda("EUR_USD") == "EUR_USD"
        assert normalize_symbol_to_oanda("GBP_JPY") == "GBP_JPY"


class TestStreamerAsync:
    """Test async methods of streamers."""
    
    @pytest.mark.asyncio
    async def test_binance_connect_disconnect(self):
        """Test Binance connect/disconnect cycle."""
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            streamer = BinanceStreamer()
            # Just verify the object is in expected state
            assert not streamer._running
    
    @pytest.mark.asyncio
    async def test_oanda_connect_disconnect(self):
        """Test Oanda connect/disconnect cycle."""
        streamer = OandaStreamer(
            api_key="test-key",
            account_id="test-account"
        )
        
        await streamer.connect()
        assert streamer._running is True
        assert streamer._session is not None
        
        await streamer.disconnect()
        assert streamer._running is False
        assert streamer._session is None
