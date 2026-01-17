"""Tests for utility helper functions."""

import pytest
from datetime import datetime, timezone

from kline_package.utils.helpers import (
    normalize_symbol_to_oanda,
    normalize_symbol_from_oanda,
    normalize_timeframe_to_oanda,
    normalize_timeframe_from_oanda,
    timestamp_to_datetime,
    VALID_TIMEFRAMES,
    TIMEFRAME_TO_OANDA,
    OANDA_TO_TIMEFRAME
)


class TestTimeframeMappings:
    """Test timeframe mapping constants."""
    
    def test_all_timeframes_have_oanda_mapping(self):
        """Test that all valid timeframes have Oanda mappings."""
        for tf in VALID_TIMEFRAMES:
            assert tf in TIMEFRAME_TO_OANDA
    
    def test_bidirectional_mapping(self):
        """Test that mappings are bidirectional."""
        for binance_tf, oanda_tf in TIMEFRAME_TO_OANDA.items():
            assert OANDA_TO_TIMEFRAME[oanda_tf] == binance_tf


class TestTimeframeNormalization:
    """Test timeframe normalization functions."""
    
    def test_to_oanda_minutes(self):
        """Test minute conversions to Oanda."""
        assert normalize_timeframe_to_oanda("1m") == "M1"
        assert normalize_timeframe_to_oanda("3m") == "M3"
        assert normalize_timeframe_to_oanda("5m") == "M5"
        assert normalize_timeframe_to_oanda("15m") == "M15"
        assert normalize_timeframe_to_oanda("30m") == "M30"
    
    def test_to_oanda_hours(self):
        """Test hourly conversions to Oanda."""
        assert normalize_timeframe_to_oanda("1h") == "H1"
        assert normalize_timeframe_to_oanda("2h") == "H2"
        assert normalize_timeframe_to_oanda("4h") == "H4"
        assert normalize_timeframe_to_oanda("6h") == "H6"
        assert normalize_timeframe_to_oanda("8h") == "H8"
        assert normalize_timeframe_to_oanda("12h") == "H12"
    
    def test_to_oanda_daily_weekly_monthly(self):
        """Test daily, weekly, monthly conversions to Oanda."""
        assert normalize_timeframe_to_oanda("1d") == "D"
        assert normalize_timeframe_to_oanda("1w") == "W"
        assert normalize_timeframe_to_oanda("1M") == "M"
    
    def test_to_oanda_already_oanda_format(self):
        """Test that Oanda format passes through."""
        assert normalize_timeframe_to_oanda("M1") == "M1"
        assert normalize_timeframe_to_oanda("H4") == "H4"
        assert normalize_timeframe_to_oanda("D") == "D"
    
    def test_to_oanda_invalid(self):
        """Test invalid timeframe raises ValueError."""
        with pytest.raises(ValueError):
            normalize_timeframe_to_oanda("2d")
        with pytest.raises(ValueError):
            normalize_timeframe_to_oanda("3h")
        with pytest.raises(ValueError):
            normalize_timeframe_to_oanda("invalid")
    
    def test_from_oanda(self):
        """Test conversion from Oanda format."""
        assert normalize_timeframe_from_oanda("M1") == "1m"
        assert normalize_timeframe_from_oanda("H1") == "1h"
        assert normalize_timeframe_from_oanda("D") == "1d"
        assert normalize_timeframe_from_oanda("W") == "1w"


class TestSymbolNormalization:
    """Test symbol normalization functions."""
    
    def test_to_oanda_6char_forex(self):
        """Test 6-character forex pairs to Oanda format."""
        assert normalize_symbol_to_oanda("EURUSD") == "EUR_USD"
        assert normalize_symbol_to_oanda("GBPJPY") == "GBP_JPY"
        assert normalize_symbol_to_oanda("USDJPY") == "USD_JPY"
        assert normalize_symbol_to_oanda("AUDUSD") == "AUD_USD"
        assert normalize_symbol_to_oanda("NZDUSD") == "NZD_USD"
        assert normalize_symbol_to_oanda("USDCAD") == "USD_CAD"
        assert normalize_symbol_to_oanda("USDCHF") == "USD_CHF"
    
    def test_to_oanda_lowercase(self):
        """Test lowercase input."""
        assert normalize_symbol_to_oanda("eurusd") == "EUR_USD"
        assert normalize_symbol_to_oanda("gbpusd") == "GBP_USD"
    
    def test_to_oanda_mixed_case(self):
        """Test mixed case input."""
        assert normalize_symbol_to_oanda("EurUsd") == "EUR_USD"
    
    def test_to_oanda_already_formatted(self):
        """Test already formatted symbols pass through."""
        assert normalize_symbol_to_oanda("EUR_USD") == "EUR_USD"
        assert normalize_symbol_to_oanda("GBP_JPY") == "GBP_JPY"
    
    def test_to_oanda_metals(self):
        """Test metal symbols (XAU, XAG)."""
        assert normalize_symbol_to_oanda("XAUUSD") == "XAU_USD"
        assert normalize_symbol_to_oanda("XAGUSD") == "XAG_USD"
        assert normalize_symbol_to_oanda("XAUEUR") == "XAU_EUR"
    
    def test_to_oanda_crypto(self):
        """Test crypto symbols."""
        assert normalize_symbol_to_oanda("BTCUSD") == "BTC_USD"
        assert normalize_symbol_to_oanda("ETHUSD") == "ETH_USD"
    
    def test_from_oanda(self):
        """Test conversion from Oanda to universal format."""
        assert normalize_symbol_from_oanda("EUR_USD") == "EURUSD"
        assert normalize_symbol_from_oanda("GBP_JPY") == "GBPJPY"
        assert normalize_symbol_from_oanda("XAU_USD") == "XAUUSD"


class TestTimestampConversion:
    """Test timestamp conversion functions."""
    
    def test_milliseconds_to_datetime(self):
        """Test converting milliseconds to datetime."""
        # 2024-01-01 00:00:00 UTC
        ms = 1704067200000
        dt = timestamp_to_datetime(ms)
        
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 0
        assert dt.tzinfo == timezone.utc
    
    def test_seconds_to_datetime(self):
        """Test converting seconds to datetime."""
        # 2024-01-01 00:00:00 UTC
        sec = 1704067200
        dt = timestamp_to_datetime(sec)
        
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
    
    def test_string_timestamp(self):
        """Test ISO string timestamp."""
        iso_str = "2024-01-01T00:00:00Z"
        dt = timestamp_to_datetime(iso_str)
        
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
    
    def test_datetime_passthrough(self):
        """Test datetime passes through unchanged."""
        original = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = timestamp_to_datetime(original)
        
        assert result == original


class TestValidTimeframes:
    """Test VALID_TIMEFRAMES constant."""
    
    def test_contains_expected_timeframes(self):
        """Test all expected timeframes are present."""
        expected = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '1w', '1M'
        ]
        for tf in expected:
            assert tf in VALID_TIMEFRAMES
    
    def test_count(self):
        """Test correct number of valid timeframes."""
        assert len(VALID_TIMEFRAMES) == 14
