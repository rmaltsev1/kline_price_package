"""
Kline Package - A Python package for fetching price data from multiple sources.

This package provides easy-to-use interfaces for:
- Fetching price data from Binance, Oanda, Polygon.io, Interactive Brokers
- Streaming real-time data via WebSocket/HTTP streaming
- Caching data in Parquet or CSV format
"""

from kline_package.__version__ import __version__
from kline_package.fetchers import BinanceFetcher, OandaFetcher, PolygonFetcher, IBKRFetcher
from kline_package.cache import ParquetCache, CSVCache

# Lazy import streamers (requires optional websockets dependency)
def __getattr__(name):
    if name == "BinanceStreamer":
        from kline_package.streamers import BinanceStreamer
        return BinanceStreamer
    elif name == "OandaStreamer":
        from kline_package.streamers import OandaStreamer
        return OandaStreamer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "__version__",
    "BinanceFetcher",
    "OandaFetcher",
    "PolygonFetcher",
    "IBKRFetcher",
    "ParquetCache",
    "CSVCache",
    "BinanceStreamer",
    "OandaStreamer",
]
