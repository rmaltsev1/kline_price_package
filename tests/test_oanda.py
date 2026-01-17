"""Tests for Oanda fetcher."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from kline_package.fetchers import OandaFetcher
from kline_package.utils.helpers import (
    normalize_symbol_to_oanda,
    normalize_timeframe_to_oanda,
    VALID_TIMEFRAMES
)


class TestOandaFetcher:
    """Test suite for OandaFetcher."""
    
    def test_initialization_practice(self):
        """Test fetcher initialization with practice account."""
        fetcher = OandaFetcher(
            api_key="test-key",
            account_id="test-account",
            practice=True
        )
        assert fetcher is not None
        assert fetcher.base_url == OandaFetcher.PRACTICE_URL
    
    def test_initialization_live(self):
        """Test fetcher initialization with live account."""
        fetcher = OandaFetcher(
            api_key="test-key",
            account_id="test-account",
            practice=False
        )
        assert fetcher.base_url == OandaFetcher.LIVE_URL

    def test_custom_base_url(self):
        """Test initialization with custom base URL."""
        custom_url = "https://custom.oanda.com"
        fetcher = OandaFetcher(
            api_key="test-key",
            account_id="test-account",
            base_url=custom_url
        )
        assert fetcher.base_url == custom_url

    def test_headers_set(self):
        """Test that authorization headers are set."""
        fetcher = OandaFetcher(
            api_key="my-api-key",
            account_id="test-account"
        )
        assert 'Authorization' in fetcher.session.headers
        assert fetcher.session.headers['Authorization'] == 'Bearer my-api-key'

    def test_invalid_timeframe(self):
        """Test that invalid timeframe raises ValueError."""
        fetcher = OandaFetcher(
            api_key="test-key",
            account_id="test-account"
        )
        with pytest.raises(ValueError, match="Invalid"):
            fetcher.fetch("EURUSD", "invalid_timeframe")


class TestSymbolNormalization:
    """Test symbol normalization for Oanda."""
    
    def test_forex_pairs(self):
        """Test standard forex pair normalization."""
        assert normalize_symbol_to_oanda("EURUSD") == "EUR_USD"
        assert normalize_symbol_to_oanda("GBPJPY") == "GBP_JPY"
        assert normalize_symbol_to_oanda("USDJPY") == "USD_JPY"
        assert normalize_symbol_to_oanda("AUDUSD") == "AUD_USD"
        assert normalize_symbol_to_oanda("NZDUSD") == "NZD_USD"
        assert normalize_symbol_to_oanda("USDCAD") == "USD_CAD"
        assert normalize_symbol_to_oanda("USDCHF") == "USD_CHF"

    def test_already_normalized(self):
        """Test that already normalized symbols pass through."""
        assert normalize_symbol_to_oanda("EUR_USD") == "EUR_USD"
        assert normalize_symbol_to_oanda("GBP_JPY") == "GBP_JPY"

    def test_lowercase_input(self):
        """Test lowercase symbol input."""
        assert normalize_symbol_to_oanda("eurusd") == "EUR_USD"
        assert normalize_symbol_to_oanda("gbpjpy") == "GBP_JPY"

    def test_metals(self):
        """Test metal symbols like XAU, XAG."""
        assert normalize_symbol_to_oanda("XAUUSD") == "XAU_USD"
        assert normalize_symbol_to_oanda("XAGUSD") == "XAG_USD"

    def test_crypto(self):
        """Test crypto symbols."""
        assert normalize_symbol_to_oanda("BTCUSD") == "BTC_USD"
        assert normalize_symbol_to_oanda("ETHUSD") == "ETH_USD"


class TestTimeframeNormalization:
    """Test timeframe normalization for Oanda."""
    
    def test_minute_timeframes(self):
        """Test minute timeframe conversions."""
        assert normalize_timeframe_to_oanda("1m") == "M1"
        assert normalize_timeframe_to_oanda("5m") == "M5"
        assert normalize_timeframe_to_oanda("15m") == "M15"
        assert normalize_timeframe_to_oanda("30m") == "M30"

    def test_hourly_timeframes(self):
        """Test hourly timeframe conversions."""
        assert normalize_timeframe_to_oanda("1h") == "H1"
        assert normalize_timeframe_to_oanda("4h") == "H4"
        assert normalize_timeframe_to_oanda("12h") == "H12"

    def test_daily_weekly_monthly(self):
        """Test daily, weekly, monthly conversions."""
        assert normalize_timeframe_to_oanda("1d") == "D"
        assert normalize_timeframe_to_oanda("1w") == "W"
        assert normalize_timeframe_to_oanda("1M") == "M"

    def test_already_oanda_format(self):
        """Test that Oanda format passes through."""
        assert normalize_timeframe_to_oanda("M1") == "M1"
        assert normalize_timeframe_to_oanda("H1") == "H1"
        assert normalize_timeframe_to_oanda("D") == "D"

    def test_invalid_timeframe(self):
        """Test that invalid timeframe raises ValueError."""
        with pytest.raises(ValueError):
            normalize_timeframe_to_oanda("2d")
        with pytest.raises(ValueError):
            normalize_timeframe_to_oanda("invalid")


class TestValidTimeframes:
    """Test valid timeframe constants."""
    
    def test_all_valid_timeframes(self):
        """Test that all expected timeframes are valid."""
        expected = ['1m', '3m', '5m', '15m', '30m', 
                    '1h', '2h', '4h', '6h', '8h', '12h',
                    '1d', '1w', '1M']
        for tf in expected:
            assert tf in VALID_TIMEFRAMES
