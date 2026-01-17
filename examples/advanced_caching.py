"""Advanced caching strategies and patterns."""

from kline_package.fetchers import BinanceFetcher, OandaFetcher
from kline_package.cache import ParquetCache, CSVCache
from datetime import datetime, timezone, timedelta
import os
import pandas as pd

def fetch_and_cache_multiple_symbols():
    """Fetch and cache data for multiple trading pairs."""
    fetcher = BinanceFetcher()
    cache = ParquetCache(cache_dir="./data/crypto")
    
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    for symbol in symbols:
        print(f"Fetching {symbol}...")
        data = fetcher.fetch(symbol=symbol, interval="1d", limit=30)
        cache.save(data, filename=f"{symbol.lower()}_daily")
        print(f"Saved {symbol} to cache ({len(data)} records)")

def compare_cache_formats():
    """Compare Parquet vs CSV cache performance and size."""
    fetcher = BinanceFetcher()
    
    # Fetch some data
    print("Fetching data for comparison...")
    data = fetcher.fetch(symbol="BTCUSDT", interval="1h", limit=1000)
    
    # Save in both formats
    parquet_cache = ParquetCache(cache_dir="./data/comparison")
    csv_cache = CSVCache(cache_dir="./data/comparison")
    
    print("\nSaving in Parquet format...")
    parquet_cache.save(data, filename="btc_comparison")
    
    print("Saving in CSV format...")
    csv_cache.save(data, filename="btc_comparison", index=False)
    
    # Check file sizes
    parquet_path = parquet_cache._get_file_path("btc_comparison")
    csv_path = csv_cache._get_file_path("btc_comparison")
    
    parquet_size = parquet_path.stat().st_size
    csv_size = csv_path.stat().st_size
    
    print(f"\nParquet size: {parquet_size:,} bytes")
    print(f"CSV size: {csv_size:,} bytes")
    print(f"Compression ratio: {csv_size/parquet_size:.2f}x")
    print(f"Space saved: {(csv_size - parquet_size):,} bytes ({100*(1-parquet_size/csv_size):.1f}%)")

def incremental_caching():
    """Example of incremental data caching."""
    fetcher = BinanceFetcher()
    cache = ParquetCache(cache_dir="./data/incremental")
    
    filename = "btc_incremental"
    
    # Check if cache exists
    if cache.exists(filename):
        print("Loading existing data...")
        existing_data = cache.load(filename)
        print(f"Found {len(existing_data)} existing records")
        print(f"Latest record: {existing_data['Open Time'].max()}")
        
        # Fetch only new data (simplified example)
        new_data = fetcher.fetch(symbol="BTCUSDT", interval="1h", limit=10)
        
        # Combine and remove duplicates
        combined_data = pd.concat([existing_data, new_data])
        combined_data = combined_data.drop_duplicates(subset=['Open Time']).sort_values('Open Time')
        
        cache.save(combined_data, filename=filename)
        print(f"Updated cache with {len(combined_data)} total records (added {len(combined_data) - len(existing_data)} new)")
    else:
        print("No existing cache, fetching initial data...")
        data = fetcher.fetch(symbol="BTCUSDT", interval="1h", limit=100)
        cache.save(data, filename=filename)
        print(f"Saved {len(data)} records to new cache")

def cache_management():
    """Example of cache file management."""
    cache = ParquetCache(cache_dir="./data/management")
    
    # Create some test data
    test_data = pd.DataFrame({
        'Open Time': pd.date_range('2024-01-01', periods=10, freq='H'),
        'Open': [100 + i for i in range(10)],
        'High': [101 + i for i in range(10)],
        'Low': [99 + i for i in range(10)],
        'Close': [100.5 + i for i in range(10)],
        'Volume': [1000 + i*10 for i in range(10)]
    })
    
    # Save multiple files
    print("Creating test cache files...")
    for i in range(3):
        cache.save(test_data, filename=f"test_file_{i}")
    
    # List all files
    print("\nCache files:")
    files = cache.list_files()
    for f in files:
        print(f"  - {f}")
    
    # Check if file exists
    print("\nChecking existence:")
    print(f"  test_file_0 exists: {cache.exists('test_file_0')}")
    print(f"  nonexistent exists: {cache.exists('nonexistent')}")
    
    # Delete a file
    print("\nDeleting test_file_1...")
    cache.delete("test_file_1")
    
    print("\nRemaining files:")
    files = cache.list_files()
    for f in files:
        print(f"  - {f}")

def main():
    """Run all examples."""
    print("=" * 60)
    print("Example 1: Multiple Symbols")
    print("=" * 60)
    try:
        fetch_and_cache_multiple_symbols()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Example 2: Cache Format Comparison")
    print("=" * 60)
    try:
        compare_cache_formats()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Example 3: Incremental Caching")
    print("=" * 60)
    try:
        incremental_caching()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Example 4: Cache Management")
    print("=" * 60)
    try:
        cache_management()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
