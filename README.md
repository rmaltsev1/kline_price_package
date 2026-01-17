# Kline Package

A Python package for fetching price data from multiple sources with flexible caching capabilities.

## Features

- 🚀 **Fetch Price Data** from multiple sources:
  - **Binance** - cryptocurrency exchange (direct API, no auth required)
  - **Oanda** - forex/CFD broker (requires API key)
  - **Polygon.io** - stocks, forex, crypto (free tier available)
  - **Interactive Brokers** - stocks, options, futures, forex
  
- 📡 **Real-time Streaming**:
  - Binance WebSocket (klines, trades, tickers, order book)
  - Oanda price streaming
  
- 💾 **Flexible Caching**:
  - Parquet format (efficient, compressed)
  - CSV format (human-readable)
  
- 🔧 **Universal Format**: Same symbol and timeframe format for all data sources
  - Symbols: `BTCUSDT`, `EURUSD`, `XAUUSD`, `AAPL` (auto-converts for each API)
  - Timeframes: `1m`, `5m`, `1h`, `4h`, `1d` (auto-converts for each API)

## Installation

```bash
pip install kline-package
```

### Optional Dependencies

```bash
# For real-time streaming
pip install kline-package[streaming]

# For Interactive Brokers
pip install kline-package[ibkr]

# Everything
pip install kline-package[all]
```

## Quick Start

### Fetching Binance Data (Crypto)

```python
from kline_package import BinanceFetcher, ParquetCache

fetcher = BinanceFetcher()
data = fetcher.fetch(symbol="BTCUSDT", interval="1h", limit=100)

cache = ParquetCache(cache_dir="./data")
cache.save(data, filename="btc_prices")
```

### Fetching Oanda Data (Forex)

```python
from kline_package import OandaFetcher

fetcher = OandaFetcher(
    api_key="your-api-key",
    account_id="your-account-id"
)

# Universal format: EURUSD -> EUR_USD, 1h -> H1 (auto-converted)
data = fetcher.fetch(symbol="EURUSD", interval="1h", count=100)
```

### Fetching Polygon.io Data (Stocks/Crypto/Forex)

```python
from kline_package import PolygonFetcher

# Free tier: 5 calls/min, delayed data
fetcher = PolygonFetcher(api_key="your-polygon-api-key")

# Fetch stock data
aapl = fetcher.fetch("AAPL", "1d", days=30)

# Fetch crypto data
btc = fetcher.fetch("X:BTCUSD", "1h", days=7)

# Fetch forex data
eur = fetcher.fetch("C:EURUSD", "1h", days=7)

# Search for tickers
results = fetcher.search_tickers("Apple", market="stocks")
```

### Fetching Interactive Brokers Data

```python
from kline_package import IBKRFetcher

# Requires TWS or IB Gateway running locally
# pip install kline-package[ibkr]

fetcher = IBKRFetcher(
    host="127.0.0.1",
    port=7497,  # 7497=TWS paper, 7496=TWS live
    client_id=1
)

# Fetch stock data
data = fetcher.fetch("AAPL", "1h", days=5)

# Fetch forex data  
fx_data = fetcher.fetch("EUR.USD", "1h", days=5, sec_type="FX")

# Clean up
fetcher.disconnect()
```

## Real-time Streaming

### Binance WebSocket

```python
import asyncio
from kline_package import BinanceStreamer

async def on_kline(data):
    print(f"{data['symbol']}: {data['close']}")

async def main():
    streamer = BinanceStreamer()
    await streamer.connect()
    await streamer.subscribe_kline("BTCUSDT", "1m", on_kline)
    
    await asyncio.sleep(60)
    await streamer.disconnect()

asyncio.run(main())
```

### Oanda Streaming

```python
import asyncio
from kline_package import OandaStreamer

async def on_price(data):
    print(f"{data['symbol']}: Bid={data['bid']}, Ask={data['ask']}")

async def main():
    streamer = OandaStreamer(
        api_key="your-api-key",
        account_id="your-account-id"
    )
    await streamer.connect()
    await streamer.subscribe("EURUSD", on_price)  # Universal format
    
    await asyncio.sleep(60)
    await streamer.disconnect()

asyncio.run(main())
```

## Universal Timeframes

| Universal | Binance | Oanda | Polygon |
|-----------|---------|-------|---------|
| `1m`      | 1m      | M1    | 1 minute |
| `5m`      | 5m      | M5    | 5 minute |
| `15m`     | 15m     | M15   | 15 minute |
| `1h`      | 1h      | H1    | 1 hour |
| `4h`      | 4h      | H4    | 4 hour |
| `1d`      | 1d      | D     | 1 day |
| `1w`      | 1w      | W     | 1 week |

## Caching

```python
from kline_package import ParquetCache, CSVCache

# Parquet (recommended for large datasets)
cache = ParquetCache(cache_dir="./data")
cache.save(df, "my_data")
loaded = cache.load("my_data")

# CSV (human-readable)
cache = CSVCache(cache_dir="./data")
cache.save(df, "my_data")
loaded = cache.load("my_data")

# Check if exists
if cache.exists("my_data"):
    df = cache.load("my_data")

# List cached files
files = cache.list_files()

# Delete
cache.delete("my_data")
```

## API Reference

### Fetchers

| Class | Source | Auth Required |
|-------|--------|---------------|
| `BinanceFetcher` | Binance | No |
| `OandaFetcher` | Oanda | API Key + Account ID |
| `PolygonFetcher` | Polygon.io | API Key |
| `IBKRFetcher` | Interactive Brokers | TWS/Gateway |

### Streamers

| Class | Source | Auth Required |
|-------|--------|---------------|
| `BinanceStreamer` | Binance WebSocket | No |
| `OandaStreamer` | Oanda Streaming | API Key + Account ID |

### Caches

| Class | Format | Best For |
|-------|--------|----------|
| `ParquetCache` | .parquet | Large datasets, fast I/O |
| `CSVCache` | .csv | Human-readable, debugging |

## License

MIT License - see LICENSE file for details.
