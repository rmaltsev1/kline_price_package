"""Oanda streaming client for real-time price data."""

import asyncio
import json
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime, timezone

import requests

from kline_package.streamers.base import BaseStreamer
from kline_package.utils.helpers import normalize_symbol_to_oanda


class OandaStreamer(BaseStreamer):
    """
    Streaming client for Oanda real-time price data.
    
    Uses Oanda's streaming API to receive real-time price updates.
    
    Example:
        ```python
        import asyncio
        from kline_package.streamers import OandaStreamer
        
        async def on_price(data):
            print(f"Price: {data}")
        
        async def main():
            streamer = OandaStreamer(
                api_key="your-api-key",
                account_id="your-account-id"
            )
            await streamer.connect()
            await streamer.subscribe("EURUSD", on_price)
            
            # Keep running for 60 seconds
            await asyncio.sleep(60)
            await streamer.disconnect()
        
        asyncio.run(main())
        ```
    """
    
    PRACTICE_STREAM_URL = "https://stream-fxpractice.oanda.com"
    LIVE_STREAM_URL = "https://stream-fxtrade.oanda.com"
    
    def __init__(
        self,
        api_key: str,
        account_id: str,
        practice: bool = True,
        base_url: Optional[str] = None
    ):
        """
        Initialize the Oanda streaming client.
        
        Args:
            api_key: Oanda API key
            account_id: Oanda account ID
            practice: Whether to use practice account (default: True)
            base_url: Optional custom streaming URL
        """
        super().__init__()
        self.api_key = api_key
        self.account_id = account_id
        
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = self.PRACTICE_STREAM_URL if practice else self.LIVE_STREAM_URL
        
        self._session: Optional[requests.Session] = None
        self._response: Optional[requests.Response] = None
        self._subscriptions: Dict[str, Callable] = {}
        self._instruments: List[str] = []
        self._listen_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """
        Initialize the streaming session.
        
        Note: Actual connection is made when subscribing to instruments.
        """
        self._session = requests.Session()
        self._session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        })
        self._running = True
    
    async def disconnect(self) -> None:
        """Close the streaming connection."""
        self._running = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self._response:
            self._response.close()
            self._response = None
        
        if self._session:
            self._session.close()
            self._session = None
        
        self._subscriptions.clear()
        self._instruments.clear()
        self._handle_close()
    
    async def subscribe(
        self, 
        symbol: str, 
        callback: Callable[[dict], None],
        **kwargs
    ) -> None:
        """
        Subscribe to price updates for a symbol.
        
        Args:
            symbol: Symbol in universal format (e.g., 'EURUSD')
            callback: Function to call when price data is received
            
        The callback receives a dict with:
            - symbol: Instrument name
            - time: Price timestamp (datetime)
            - bid: Bid price
            - ask: Ask price
            - spread: Ask - Bid
            - mid: Midpoint price
        """
        # Convert to Oanda format
        instrument = normalize_symbol_to_oanda(symbol)
        
        self._subscriptions[instrument] = callback
        
        if instrument not in self._instruments:
            self._instruments.append(instrument)
            await self._restart_stream()
    
    async def unsubscribe(self, symbol: str, **kwargs) -> None:
        """
        Unsubscribe from price updates for a symbol.
        
        Args:
            symbol: Symbol in universal format (e.g., 'EURUSD')
        """
        instrument = normalize_symbol_to_oanda(symbol)
        
        if instrument in self._subscriptions:
            del self._subscriptions[instrument]
        
        if instrument in self._instruments:
            self._instruments.remove(instrument)
            await self._restart_stream()
    
    async def subscribe_transactions(self, callback: Callable[[dict], None]) -> None:
        """
        Subscribe to account transaction updates.
        
        Args:
            callback: Function to call when transaction occurs
        """
        self._subscriptions['__transactions__'] = callback
        
        # Start transaction stream in separate task
        asyncio.create_task(self._stream_transactions(callback))
    
    async def _restart_stream(self) -> None:
        """Restart the price stream with updated instruments."""
        # Cancel existing listen task
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        # Close existing response
        if self._response:
            self._response.close()
            self._response = None
        
        # Start new stream if we have instruments
        if self._instruments and self._running:
            self._listen_task = asyncio.create_task(self._listen())
    
    async def _listen(self) -> None:
        """Listen for incoming price updates."""
        if not self._session or not self._instruments:
            return
        
        url = f"{self.base_url}/v3/accounts/{self.account_id}/pricing/stream"
        params = {
            'instruments': ','.join(self._instruments)
        }
        
        try:
            # Run blocking request in executor
            loop = asyncio.get_event_loop()
            self._response = await loop.run_in_executor(
                None,
                lambda: self._session.get(url, params=params, stream=True, timeout=None)
            )
            
            if self._response.status_code != 200:
                error_text = self._response.text
                raise ConnectionError(f"Failed to connect to Oanda stream: {error_text}")
            
            # Process streaming response
            for line in self._response.iter_lines():
                if not self._running:
                    break
                
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        await self._handle_message(data)
                    except json.JSONDecodeError as e:
                        self._handle_error(e)
                        
        except asyncio.CancelledError:
            pass
        except requests.exceptions.RequestException as e:
            self._handle_error(e)
        except Exception as e:
            self._handle_error(e)
        finally:
            if self._response:
                self._response.close()
    
    async def _handle_message(self, data: dict) -> None:
        """Process incoming message and dispatch to callbacks."""
        msg_type = data.get('type')
        
        # Call general message callback
        if 'message' in self._callbacks:
            await self._maybe_await(self._callbacks['message'], data)
        
        if msg_type == 'PRICE':
            instrument = data.get('instrument')
            
            if instrument in self._subscriptions:
                processed = self._process_price(data)
                callback = self._subscriptions[instrument]
                await self._maybe_await(callback, processed)
        
        elif msg_type == 'HEARTBEAT':
            # Heartbeat messages - can be ignored or logged
            pass
    
    async def _stream_transactions(self, callback: Callable[[dict], None]) -> None:
        """Stream account transactions."""
        if not self._session:
            return
        
        url = f"{self.base_url}/v3/accounts/{self.account_id}/transactions/stream"
        
        try:
            response = self._session.get(url, stream=True, timeout=None)
            
            if response.status_code != 200:
                raise ConnectionError(f"Failed to connect to transaction stream: {response.text}")
            
            for line in response.iter_lines():
                if not self._running:
                    break
                
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if data.get('type') != 'HEARTBEAT':
                            await self._maybe_await(callback, data)
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            self._handle_error(e)
    
    async def _maybe_await(self, func: Callable, *args) -> Any:
        """Call a function, awaiting if it's a coroutine."""
        result = func(*args)
        if asyncio.iscoroutine(result):
            return await result
        return result
    
    def _process_price(self, data: dict) -> dict:
        """Process raw price message into clean format."""
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        bid = float(bids[0]['price']) if bids else 0.0
        ask = float(asks[0]['price']) if asks else 0.0
        
        return {
            'symbol': data.get('instrument', ''),
            'time': datetime.fromisoformat(data.get('time', '').replace('Z', '+00:00')),
            'bid': bid,
            'ask': ask,
            'spread': ask - bid,
            'mid': (bid + ask) / 2,
            'tradeable': data.get('tradeable', False),
        }
