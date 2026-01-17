"""Binance WebSocket streamer for real-time data."""

import asyncio
import json
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime, timezone

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketClientProtocol = Any

from kline_package.streamers.base import BaseStreamer
from kline_package.utils.helpers import VALID_TIMEFRAMES


class BinanceStreamer(BaseStreamer):
    """
    WebSocket streamer for Binance real-time data.
    
    Supports streaming of:
    - Kline/Candlestick data
    - Trade data
    - Ticker data
    - Order book updates
    
    Example:
        ```python
        import asyncio
        from kline_package.streamers import BinanceStreamer
        
        async def on_kline(data):
            print(f"Kline: {data}")
        
        async def main():
            streamer = BinanceStreamer()
            await streamer.connect()
            await streamer.subscribe_kline("BTCUSDT", "1m", on_kline)
            
            # Keep running for 60 seconds
            await asyncio.sleep(60)
            await streamer.disconnect()
        
        asyncio.run(main())
        ```
    """
    
    BASE_WS_URL = "wss://stream.binance.com:9443/ws"
    COMBINED_WS_URL = "wss://stream.binance.com:9443/stream"
    
    VALID_INTERVALS = VALID_TIMEFRAMES
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Binance WebSocket streamer.
        
        Args:
            base_url: Optional custom WebSocket URL
        """
        if not HAS_WEBSOCKETS:
            raise ImportError(
                "websockets library is required for streaming. "
                "Install it with: pip install websockets"
            )
        
        super().__init__()
        self.base_url = base_url or self.BASE_WS_URL
        self._ws: Optional[WebSocketClientProtocol] = None
        self._subscriptions: Dict[str, Callable] = {}
        self._listen_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """
        Establish WebSocket connection to Binance.
        
        Raises:
            ConnectionError: If connection cannot be established
        """
        try:
            self._ws = await websockets.connect(self.base_url)
            self._running = True
            self._listen_task = asyncio.create_task(self._listen())
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Binance WebSocket: {e}")
    
    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._running = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._handle_close()
    
    async def subscribe(
        self, 
        symbol: str, 
        callback: Callable[[dict], None],
        stream_type: str = "kline",
        interval: str = "1m"
    ) -> None:
        """
        Subscribe to a data stream.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            callback: Async function to call when data is received
            stream_type: Type of stream ('kline', 'trade', 'ticker', 'depth')
            interval: Kline interval (only for kline stream)
        """
        if stream_type == "kline":
            await self.subscribe_kline(symbol, interval, callback)
        elif stream_type == "trade":
            await self.subscribe_trade(symbol, callback)
        elif stream_type == "ticker":
            await self.subscribe_ticker(symbol, callback)
        elif stream_type == "depth":
            await self.subscribe_depth(symbol, callback)
        else:
            raise ValueError(f"Unknown stream type: {stream_type}")
    
    async def subscribe_kline(
        self, 
        symbol: str, 
        interval: str, 
        callback: Callable[[dict], None]
    ) -> None:
        """
        Subscribe to kline/candlestick stream.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '1m', '1h', '1d')
            callback: Async function to call with kline data
            
        The callback receives a dict with:
            - symbol: Trading symbol
            - interval: Kline interval
            - open_time: Kline open time (datetime)
            - open: Open price
            - high: High price
            - low: Low price
            - close: Close price
            - volume: Trading volume
            - close_time: Kline close time (datetime)
            - is_closed: Whether the kline is closed
        """
        if interval not in self.VALID_INTERVALS:
            raise ValueError(f"Invalid interval. Valid options: {self.VALID_INTERVALS}")
        
        stream_name = f"{symbol.lower()}@kline_{interval}"
        await self._subscribe_stream(stream_name, callback, self._process_kline)
    
    async def subscribe_trade(
        self, 
        symbol: str, 
        callback: Callable[[dict], None]
    ) -> None:
        """
        Subscribe to trade stream.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            callback: Async function to call with trade data
        """
        stream_name = f"{symbol.lower()}@trade"
        await self._subscribe_stream(stream_name, callback, self._process_trade)
    
    async def subscribe_ticker(
        self, 
        symbol: str, 
        callback: Callable[[dict], None]
    ) -> None:
        """
        Subscribe to 24hr ticker stream.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            callback: Async function to call with ticker data
        """
        stream_name = f"{symbol.lower()}@ticker"
        await self._subscribe_stream(stream_name, callback, self._process_ticker)
    
    async def subscribe_depth(
        self, 
        symbol: str, 
        callback: Callable[[dict], None],
        levels: int = 10
    ) -> None:
        """
        Subscribe to order book depth stream.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            callback: Async function to call with depth data
            levels: Number of levels (5, 10, or 20)
        """
        stream_name = f"{symbol.lower()}@depth{levels}"
        await self._subscribe_stream(stream_name, callback, self._process_depth)
    
    async def unsubscribe(self, symbol: str, stream_type: str = "kline", interval: str = "1m") -> None:
        """
        Unsubscribe from a stream.
        
        Args:
            symbol: Trading symbol
            stream_type: Type of stream
            interval: Kline interval (for kline streams)
        """
        if stream_type == "kline":
            stream_name = f"{symbol.lower()}@kline_{interval}"
        elif stream_type == "trade":
            stream_name = f"{symbol.lower()}@trade"
        elif stream_type == "ticker":
            stream_name = f"{symbol.lower()}@ticker"
        else:
            stream_name = f"{symbol.lower()}@{stream_type}"
        
        if stream_name in self._subscriptions:
            del self._subscriptions[stream_name]
            
            # Send unsubscribe message
            if self._ws:
                msg = {
                    "method": "UNSUBSCRIBE",
                    "params": [stream_name],
                    "id": hash(stream_name)
                }
                await self._ws.send(json.dumps(msg))
    
    async def _subscribe_stream(
        self, 
        stream_name: str, 
        callback: Callable[[dict], None],
        processor: Callable[[dict], dict]
    ) -> None:
        """Internal method to subscribe to a stream."""
        self._subscriptions[stream_name] = (callback, processor)
        
        if self._ws:
            msg = {
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": hash(stream_name)
            }
            await self._ws.send(json.dumps(msg))
    
    async def _listen(self) -> None:
        """Listen for incoming WebSocket messages."""
        try:
            while self._running and self._ws:
                try:
                    message = await self._ws.recv()
                    data = json.loads(message)
                    
                    # Skip subscription confirmations
                    if 'result' in data or 'id' in data:
                        continue
                    
                    await self._handle_message(data)
                    
                except websockets.ConnectionClosed:
                    self._handle_close()
                    break
                except json.JSONDecodeError as e:
                    self._handle_error(e)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._handle_error(e)
    
    async def _handle_message(self, data: dict) -> None:
        """Process incoming message and dispatch to callbacks."""
        # Call general message callback
        if 'message' in self._callbacks:
            await self._maybe_await(self._callbacks['message'], data)
        
        # Determine stream name from message
        stream_name = None
        if 'e' in data:  # Event type
            event = data['e']
            symbol = data.get('s', '').lower()
            
            if event == 'kline':
                interval = data['k']['i']
                stream_name = f"{symbol}@kline_{interval}"
            elif event == 'trade':
                stream_name = f"{symbol}@trade"
            elif event == '24hrTicker':
                stream_name = f"{symbol}@ticker"
            elif event == 'depthUpdate':
                stream_name = f"{symbol}@depth"
        
        # Dispatch to subscription callback
        if stream_name and stream_name in self._subscriptions:
            callback, processor = self._subscriptions[stream_name]
            processed_data = processor(data)
            await self._maybe_await(callback, processed_data)
    
    async def _maybe_await(self, func: Callable, *args) -> Any:
        """Call a function, awaiting if it's a coroutine."""
        result = func(*args)
        if asyncio.iscoroutine(result):
            return await result
        return result
    
    def _process_kline(self, data: dict) -> dict:
        """Process raw kline message into clean format."""
        k = data['k']
        return {
            'symbol': data['s'],
            'interval': k['i'],
            'open_time': datetime.fromtimestamp(k['t'] / 1000, tz=timezone.utc),
            'open': float(k['o']),
            'high': float(k['h']),
            'low': float(k['l']),
            'close': float(k['c']),
            'volume': float(k['v']),
            'close_time': datetime.fromtimestamp(k['T'] / 1000, tz=timezone.utc),
            'quote_volume': float(k['q']),
            'trades': k['n'],
            'is_closed': k['x'],
        }
    
    def _process_trade(self, data: dict) -> dict:
        """Process raw trade message into clean format."""
        return {
            'symbol': data['s'],
            'trade_id': data['t'],
            'price': float(data['p']),
            'quantity': float(data['q']),
            'time': datetime.fromtimestamp(data['T'] / 1000, tz=timezone.utc),
            'is_buyer_maker': data['m'],
        }
    
    def _process_ticker(self, data: dict) -> dict:
        """Process raw ticker message into clean format."""
        return {
            'symbol': data['s'],
            'price_change': float(data['p']),
            'price_change_percent': float(data['P']),
            'last_price': float(data['c']),
            'open_price': float(data['o']),
            'high_price': float(data['h']),
            'low_price': float(data['l']),
            'volume': float(data['v']),
            'quote_volume': float(data['q']),
        }
    
    def _process_depth(self, data: dict) -> dict:
        """Process raw depth message into clean format."""
        return {
            'symbol': data.get('s', ''),
            'bids': [[float(p), float(q)] for p, q in data.get('b', data.get('bids', []))],
            'asks': [[float(p), float(q)] for p, q in data.get('a', data.get('asks', []))],
        }
