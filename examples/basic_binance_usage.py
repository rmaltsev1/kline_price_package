"""Basic example of fetching data from Binance."""

from kline_package.fetchers import BinanceFetcher
from kline_package.cache import ParquetCache
from datetime import datetime, timezone

def main():
    # Initialize fetcher
    fetcher = BinanceFetcher()
    
    # Fetch Bitcoin price data (last 100 hourly candles)
    print("Fetching BTC/USDT data from Binance...")
    data = fetcher.fetch(
        symbol="BTCUSDT",
        interval="1h",
        limit=100
    )
    
    print(f"Fetched {len(data)} records")
    print("\nFirst 5 rows:")
    print(data.head())
    print("\nColumns:", data.columns.tolist())
    
    # Save to cache
    print("\nSaving to Parquet cache...")
    cache = ParquetCache(cache_dir="./data")
    cache.save(data, filename="btc_hourly")
    print("Data saved successfully!")
    
    # Load from cache
    print("\nLoading from cache...")
    loaded_data = cache.load("btc_hourly")
    print(f"Loaded {len(loaded_data)} records")
    
    # Example with date range (using timestamps in milliseconds)
    print("\n--- Fetching with date range ---")
    start_time = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end_time = int(datetime(2024, 1, 7, tzinfo=timezone.utc).timestamp() * 1000)
    
    data_range = fetcher.fetch(
        symbol="BTCUSDT",
        interval="1d",
        start_time=start_time,
        end_time=end_time
    )
    print(f"Fetched {len(data_range)} daily candles for date range")

if __name__ == "__main__":
    main()
