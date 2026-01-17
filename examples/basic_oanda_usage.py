"""Basic example of fetching data from Oanda."""

from kline_package.fetchers import OandaFetcher
from kline_package.cache import CSVCache
import os

def main():
    # Get credentials from environment variables
    api_key = os.getenv("OANDA_API_KEY", "your-api-key-here")
    account_id = os.getenv("OANDA_ACCOUNT_ID", "your-account-id-here")
    
    if api_key == "your-api-key-here" or account_id == "your-account-id-here":
        print("Please set OANDA_API_KEY and OANDA_ACCOUNT_ID environment variables")
        print("Or replace the default values in the code")
        return
    
    # Initialize fetcher (using practice account)
    fetcher = OandaFetcher(
        api_key=api_key,
        account_id=account_id,
        practice=True
    )
    
    # Fetch EUR/USD data using universal format (EURUSD, not EUR_USD)
    print("Fetching EURUSD data from Oanda...")
    data = fetcher.fetch(
        symbol="EURUSD",      # Universal format (auto-converts to EUR_USD)
        interval="1h",         # Universal format (auto-converts to H1)
        count=100
    )
    
    print(f"Fetched {len(data)} records")
    print("\nFirst 5 rows:")
    print(data.head())
    print("\nColumns:", data.columns.tolist())
    
    # Save to CSV cache
    print("\nSaving to CSV cache...")
    cache = CSVCache(cache_dir="./data")
    cache.save(data, filename="eurusd_hourly", index=False)
    print("Data saved successfully!")
    
    # Load from cache
    print("\nLoading from cache...")
    loaded_data = cache.load("eurusd_hourly", index_col=None)
    print(f"Loaded {len(loaded_data)} records")
    
    # Example with date range (RFC3339 format)
    print("\n--- Fetching with date range ---")
    data_range = fetcher.fetch(
        symbol="EURUSD",       # Universal format
        interval="1d",          # Universal format (auto-converts to D)
        from_time="2024-01-01T00:00:00.000000Z",
        to_time="2024-01-31T23:59:59.999999Z"
    )
    print(f"Fetched {len(data_range)} daily candles for January 2024")
    
    # Get available instruments
    print("\n--- Available instruments ---")
    try:
        instruments = fetcher.get_instruments()
        print(f"Found {len(instruments)} instruments")
        print("First 10:", instruments[:10])
    except Exception as e:
        print(f"Could not fetch instruments: {e}")

if __name__ == "__main__":
    main()
