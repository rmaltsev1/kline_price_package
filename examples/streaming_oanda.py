"""Example of streaming real-time price data from Oanda."""

import asyncio
import os
from kline_package.streamers import OandaStreamer


async def on_price(data: dict):
    """Handle incoming price data."""
    print(f"[{data['symbol']}] Bid: {data['bid']:.5f} | Ask: {data['ask']:.5f} | "
          f"Spread: {data['spread']*10000:.1f} pips | Mid: {data['mid']:.5f}")


async def main():
    """Run the streaming example."""
    print("=" * 60)
    print("Oanda Price Streaming Example")
    print("=" * 60)
    
    # Get credentials from environment
    api_key = os.getenv("OANDA_API_KEY", "your-api-key-here")
    account_id = os.getenv("OANDA_ACCOUNT_ID", "your-account-id-here")
    
    if api_key == "your-api-key-here" or account_id == "your-account-id-here":
        print("\nPlease set OANDA_API_KEY and OANDA_ACCOUNT_ID environment variables")
        print("Or replace the default values in the code")
        return
    
    streamer = OandaStreamer(
        api_key=api_key,
        account_id=account_id,
        practice=True
    )
    
    try:
        # Connect to Oanda streaming
        print("\nConnecting to Oanda streaming API...")
        await streamer.connect()
        print("Connected!\n")
        
        # Subscribe to price streams (using universal format)
        print("Subscribing to price streams...")
        
        await streamer.subscribe("EURUSD", on_price)
        print("  - EURUSD")
        
        await streamer.subscribe("GBPUSD", on_price)
        print("  - GBPUSD")
        
        await streamer.subscribe("XAUUSD", on_price)
        print("  - XAUUSD (Gold)")
        
        print("\nStreaming prices for 30 seconds...\n")
        print("-" * 60)
        
        # Keep running for 30 seconds
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nDisconnecting...")
        await streamer.disconnect()
        print("Disconnected!")


if __name__ == "__main__":
    asyncio.run(main())
