#!/usr/bin/env python3
"""
Binance WebSocket Streaming Demo
================================
Run this file to see real-time Binance data streaming.

Usage:
    python run_binance_stream.py

The script will stream:
1. BTCUSDT 1-minute kline/candlestick data
2. BTCUSDT trades
3. BTCUSDT 24h ticker

Press Ctrl+C to stop.
"""

import asyncio
import sys
from datetime import datetime

try:
    from kline_package.streamers import BinanceStreamer
except ImportError:
    print("Error: websockets package not installed.")
    print("Run: pip install kline-package[streaming]")
    sys.exit(1)


# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Print the demo header."""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("  Binance WebSocket Streaming Demo")
    print(f"{'='*60}{Colors.RESET}\n")


async def on_kline(data: dict):
    """Handle incoming kline data."""
    symbol = data.get('symbol', 'N/A')
    close = data.get('close', 'N/A')
    high = data.get('high', 'N/A')
    low = data.get('low', 'N/A')
    volume = data.get('volume', 'N/A')
    is_closed = data.get('is_closed', False)
    
    status = f"{Colors.GREEN}CLOSED{Colors.RESET}" if is_closed else f"{Colors.YELLOW}OPEN{Colors.RESET}"
    print(f"{Colors.CYAN}[KLINE]{Colors.RESET} {symbol} | "
          f"Close: {close} | High: {high} | Low: {low} | "
          f"Vol: {volume:.2f} | {status}")


async def on_trade(data: dict):
    """Handle incoming trade data."""
    symbol = data.get('symbol', 'N/A')
    price = data.get('price', 'N/A')
    qty = data.get('quantity', 'N/A')
    is_buyer_maker = data.get('is_buyer_maker', False)
    
    side = f"{Colors.RED}SELL{Colors.RESET}" if is_buyer_maker else f"{Colors.GREEN}BUY{Colors.RESET}"
    print(f"{Colors.BLUE}[TRADE]{Colors.RESET} {symbol} | "
          f"Price: {price} | Qty: {qty} | {side}")


async def on_ticker(data: dict):
    """Handle incoming 24h ticker data."""
    symbol = data.get('symbol', 'N/A')
    price_change = data.get('price_change', 0)
    price_change_pct = data.get('price_change_percent', 0)
    last_price = data.get('last_price', 'N/A')
    high = data.get('high_price', 'N/A')
    low = data.get('low_price', 'N/A')
    volume = data.get('volume', 'N/A')
    
    try:
        pct = float(price_change_pct)
        color = Colors.GREEN if pct >= 0 else Colors.RED
        pct_str = f"{color}{pct:+.2f}%{Colors.RESET}"
    except (ValueError, TypeError):
        pct_str = f"{price_change_pct}%"
    
    print(f"{Colors.YELLOW}[24H TICKER]{Colors.RESET} {symbol} | "
          f"Price: {last_price} | Change: {pct_str} | "
          f"High: {high} | Low: {low} | Vol: {volume}")


async def main():
    """Main function to run the streaming demo."""
    print_header()
    
    symbol = "BTCUSDT"
    
    print(f"Connecting to Binance WebSocket...")
    print(f"Symbol: {symbol}")
    print(f"Streams: kline@1m, trades, 24h ticker")
    print(f"\n{Colors.BOLD}Press Ctrl+C to stop{Colors.RESET}\n")
    print("-" * 60)
    
    streamer = BinanceStreamer()
    
    try:
        await streamer.connect()
        print(f"{Colors.GREEN}✓ Connected to Binance WebSocket{Colors.RESET}\n")
        
        # Subscribe to multiple streams
        await streamer.subscribe_kline(symbol, "1m", on_kline)
        await streamer.subscribe_trade(symbol, on_trade)
        await streamer.subscribe_ticker(symbol, on_ticker)
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Stopping...{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
    finally:
        await streamer.disconnect()
        print(f"{Colors.GREEN}✓ Disconnected{Colors.RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
