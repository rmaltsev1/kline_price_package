"""Example of streaming real-time data from Binance WebSocket."""

import asyncio
from kline_package.streamers import BinanceStreamer


async def on_kline(data: dict):
    """Handle incoming kline data."""
    print(f"[{data['symbol']}] {data['interval']} Kline:")
    print(f"  Time: {data['open_time']}")
    print(f"  O: {data['open']:.2f} H: {data['high']:.2f} L: {data['low']:.2f} C: {data['close']:.2f}")
    print(f"  Volume: {data['volume']:.2f}")
    print(f"  Closed: {data['is_closed']}")
    print()


async def on_trade(data: dict):
    """Handle incoming trade data."""
    side = "SELL" if data['is_buyer_maker'] else "BUY"
    print(f"[{data['symbol']}] Trade: {side} {data['quantity']:.4f} @ {data['price']:.2f}")


async def on_ticker(data: dict):
    """Handle incoming ticker data."""
    print(f"[{data['symbol']}] 24hr: {data['price_change_percent']:+.2f}% | Last: {data['last_price']:.2f}")


async def main():
    """Run the streaming example."""
    print("=" * 60)
    print("Binance WebSocket Streaming Example")
    print("=" * 60)
    
    streamer = BinanceStreamer()
    
    try:
        # Connect to Binance WebSocket
        print("\nConnecting to Binance WebSocket...")
        await streamer.connect()
        print("Connected!\n")
        
        # Subscribe to multiple streams
        print("Subscribing to streams...")
        
        # Kline stream for BTC
        await streamer.subscribe_kline("BTCUSDT", "1m", on_kline)
        print("  - BTCUSDT 1m klines")
        
        # Trade stream for ETH
        await streamer.subscribe_trade("ETHUSDT", on_trade)
        print("  - ETHUSDT trades")
        
        # Ticker stream for BNB
        await streamer.subscribe_ticker("BNBUSDT", on_ticker)
        print("  - BNBUSDT 24hr ticker")
        
        print("\nStreaming data for 30 seconds...\n")
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
