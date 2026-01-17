"""Configuration settings for the package."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class BinanceConfig:
    """Configuration for Binance API."""
    base_url: str = "https://api.binance.com"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class OandaConfig:
    """Configuration for Oanda API."""
    practice_url: str = "https://api-fxpractice.oanda.com"
    live_url: str = "https://api-fxtrade.oanda.com"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class CacheConfig:
    """Configuration for cache handlers."""
    default_dir: str = "./cache"
    parquet_compression: str = "snappy"
    csv_include_index: bool = True
