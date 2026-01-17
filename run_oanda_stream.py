#!/usr/bin/env python3
"""
Oanda Price Streaming Demo
==========================
Run this file to see real-time Oanda price data streaming.

Usage:
    1. Set your API credentials as environment variables:
       export OANDA_API_KEY="your-api-key"
       export OANDA_ACCOUNT_ID="your-account-id"
    
    2. Run the script:
       python run_oanda_stream.py

The script will stream:
- EUR/USD prices
- GBP/USD prices  
- USD/JPY prices

Press Ctrl+C to stop.
"""

import asyncio
import os
import sys
from datetime import datetime

from kline_package.streamers import OandaStreamer


# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Print the demo header."""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("  Oanda Price Streaming Demo")
    print(f"{'='*60}{Colors.RESET}\n")


def get_credentials():
    """Get Oanda API credentials from environment or prompt."""
    api_key = os.environ.get('OANDA_API_KEY')
    account_id = os.environ.get('OANDA_ACCOUNT_ID')
    
    if not api_key:
        print(f"{Colors.YELLOW}OANDA_API_KEY not found in environment{Colors.RESET}")
        api_key = input("Enter your Oanda API Key: ").strip()
    
    if not account_id:
        print(f"{Colors.YELLOW}OANDA_ACCOUNT_ID not found in environment{Colors.RESET}")
        account_id = input("Enter your Oanda Account ID: ").strip()
    
    if not api_key or not account_id:
        print(f"\n{Colors.RED}Error: API key and Account ID are required{Colors.RESET}")
        print("\nSet environment variables:")
        print("  export OANDA_API_KEY='your-api-key'")
        print("  export OANDA_ACCOUNT_ID='your-account-id'")
        sys.exit(1)
    
    return api_key, account_id


# Price tracking for color changes
last_prices = {}


async def on_price(data: dict):
    """Handle incoming price data."""
    global last_prices
    
    instrument = data.get('symbol', data.get('instrument', 'N/A'))
    time = data.get('time', 'N/A')
    bid = data.get('bid')
    ask = data.get('ask')
    spread = data.get('spread')
    mid = data.get('mid')
    
    if bid is None or ask is None:
        return
    
    # Determine price direction
    last_mid = last_prices.get(instrument)
    if last_mid is not None and mid is not None:
        if mid > last_mid:
            direction = f"{Colors.GREEN}▲{Colors.RESET}"
        elif mid < last_mid:
            direction = f"{Colors.RED}▼{Colors.RESET}"
        else:
            direction = " "
    else:
        direction = " "
    
    if mid is not None:
        last_prices[instrument] = mid
    
    # Format the timestamp
    if isinstance(time, datetime):
        time_str = time.strftime("%H:%M:%S")
    else:
        time_str = str(time)[:19] if time else "N/A"
    
    # Format spread in pips
    spread_pips = spread * 10000 if spread else 0  # For most pairs
    
    print(f"{Colors.CYAN}[{time_str}]{Colors.RESET} "
          f"{Colors.BOLD}{instrument:<10}{Colors.RESET} {direction} | "
          f"Bid: {Colors.RED}{bid:.5f}{Colors.RESET} | "
          f"Ask: {Colors.GREEN}{ask:.5f}{Colors.RESET} | "
          f"Spread: {Colors.YELLOW}{spread_pips:.1f} pips{Colors.RESET}")


async def on_heartbeat(data: dict):
    """Handle heartbeat messages."""
    time = data.get('time', 'N/A')
    print(f"{Colors.MAGENTA}[HEARTBEAT]{Colors.RESET} {time}")


async def main():
    """Main function to run the streaming demo."""
    print_header()
    
    api_key, account_id = get_credentials()
    
    # Symbols to stream (universal format - will be normalized)
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    print(f"\n{Colors.GREEN}✓ Credentials loaded{Colors.RESET}")
    print(f"Account: {account_id[:10]}...")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"\n{Colors.BOLD}Press Ctrl+C to stop{Colors.RESET}\n")
    print("-" * 70)
    
    streamer = OandaStreamer(
        api_key=api_key,
        account_id=account_id,
        practice=True  # Change to False for live account
    )
    
    try:
        await streamer.connect()
        print(f"{Colors.GREEN}✓ Connected to Oanda{Colors.RESET}\n")
        
        # Subscribe to each symbol
        for symbol in symbols:
            await streamer.subscribe(symbol, on_price)
            print(f"  Subscribed to {symbol}")
        
        print()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Stopping...{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
    finally:
        await streamer.disconnect()
        print(f"{Colors.GREEN}✓ Disconnected{Colors.RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
