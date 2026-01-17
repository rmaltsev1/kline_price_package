"""Interactive Brokers fetcher for stocks, options, futures, forex data."""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union, List
import pandas as pd

from kline_package.fetchers.base import BaseFetcher


class IBKRFetcher(BaseFetcher):
    """
    Fetcher for Interactive Brokers market data.
    
    Requires IBKR Client Portal API or TWS/IB Gateway running locally.
    
    Prerequisites:
        1. Have an Interactive Brokers account
        2. Download and run IB Gateway or TWS
        3. Enable API connections in TWS/Gateway settings
        4. Or use IBKR Client Portal Web API
    
    Example with Client Portal API:
        ```python
        from kline_package import IBKRFetcher
        
        # Using Client Portal API (requires authentication via browser)
        fetcher = IBKRFetcher(
            gateway_url="https://localhost:5000",
            use_client_portal=True
        )
        
        # Fetch stock data
        df = fetcher.fetch("AAPL", "1d", days=30)
        
        # Fetch forex data
        df = fetcher.fetch("EUR.USD", "1h", days=7)
        ```
    
    Example with ib_insync (recommended):
        ```python
        from kline_package import IBKRFetcher
        
        # Using ib_insync library (requires TWS/Gateway running)
        fetcher = IBKRFetcher(
            host="127.0.0.1",
            port=7497,  # 7497 for TWS paper, 7496 for live
            client_id=1
        )
        
        # Fetch data
        df = fetcher.fetch("AAPL", "1h", days=5)
        ```
    
    Note:
        This fetcher supports two modes:
        1. Client Portal API - REST API, requires browser auth
        2. ib_insync - Python library, requires TWS/Gateway
        
        Install ib_insync for the second mode:
        pip install ib_insync
    """
    
    CLIENT_PORTAL_URL = "https://localhost:5000/v1/api"
    
    # Map universal timeframes to IBKR bar sizes
    TIMEFRAME_MAP = {
        '1m': '1 min',
        '3m': '3 mins',
        '5m': '5 mins',
        '15m': '15 mins',
        '30m': '30 mins',
        '1h': '1 hour',
        '2h': '2 hours',
        '4h': '4 hours',
        '1d': '1 day',
        '1w': '1 week',
        '1M': '1 month',
    }
    
    # Duration strings for different timeframes
    DURATION_MAP = {
        '1m': '1 D',
        '3m': '1 D',
        '5m': '2 D',
        '15m': '5 D',
        '30m': '10 D',
        '1h': '30 D',
        '2h': '60 D',
        '4h': '120 D',
        '1d': '1 Y',
        '1w': '2 Y',
        '1M': '5 Y',
    }
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        gateway_url: Optional[str] = None,
        use_client_portal: bool = False,
        timeout: int = 60
    ):
        """
        Initialize the IBKR fetcher.
        
        Args:
            host: TWS/Gateway host (default: 127.0.0.1)
            port: TWS/Gateway port (7497=TWS paper, 7496=TWS live, 
                  4002=Gateway paper, 4001=Gateway live)
            client_id: Client ID for connection
            gateway_url: Client Portal API URL (if using web API)
            use_client_portal: Whether to use Client Portal API
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.gateway_url = gateway_url or self.CLIENT_PORTAL_URL
        self.use_client_portal = use_client_portal
        self.timeout = timeout
        
        self._ib = None
        self._connected = False
    
    def connect(self) -> None:
        """
        Connect to TWS/Gateway.
        
        Only needed for ib_insync mode.
        """
        if self.use_client_portal:
            return
        
        try:
            from ib_insync import IB
        except ImportError:
            raise ImportError(
                "ib_insync library required. Install with: pip install ib_insync"
            )
        
        self._ib = IB()
        self._ib.connect(self.host, self.port, clientId=self.client_id)
        self._connected = True
    
    def disconnect(self) -> None:
        """Disconnect from TWS/Gateway."""
        if self._ib and self._connected:
            self._ib.disconnect()
            self._connected = False
    
    def fetch(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        days: Optional[int] = None,
        sec_type: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD",
        what_to_show: str = "TRADES"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Interactive Brokers.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'EUR.USD')
            interval: Timeframe (e.g., '1m', '1h', '1d')
            start_date: Start date (optional, used to calculate duration)
            end_date: End date (default: now)
            days: Alternative to date range - fetch last N days
            sec_type: Security type ('STK', 'FX', 'FUT', 'OPT', 'CFD')
            exchange: Exchange ('SMART', 'NYSE', 'NASDAQ', 'IDEALPRO')
            currency: Currency (default: 'USD')
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')
            
        Returns:
            pd.DataFrame: OHLCV data
        """
        if interval not in self.TIMEFRAME_MAP:
            raise ValueError(f"Invalid interval '{interval}'. Valid: {list(self.TIMEFRAME_MAP.keys())}")
        
        if self.use_client_portal:
            return self._fetch_client_portal(symbol, interval, days or 30)
        else:
            return self._fetch_ib_insync(
                symbol, interval, start_date, end_date, days,
                sec_type, exchange, currency, what_to_show
            )
    
    def _fetch_client_portal(
        self,
        symbol: str,
        interval: str,
        days: int
    ) -> pd.DataFrame:
        """Fetch using Client Portal API."""
        import requests
        
        # First, search for the contract
        search_url = f"{self.gateway_url}/iserver/secdef/search"
        search_resp = requests.post(
            search_url,
            json={"symbol": symbol},
            verify=False,
            timeout=self.timeout
        )
        search_resp.raise_for_status()
        contracts = search_resp.json()
        
        if not contracts:
            raise ValueError(f"Symbol not found: {symbol}")
        
        conid = contracts[0].get("conid")
        
        # Map interval to period
        period_map = {
            '1m': '1d',
            '5m': '1w',
            '15m': '1w',
            '30m': '1m',
            '1h': '1m',
            '4h': '3m',
            '1d': '1y',
            '1w': '5y',
        }
        period = period_map.get(interval, '1m')
        
        # Fetch market data
        url = f"{self.gateway_url}/iserver/marketdata/history"
        params = {
            "conid": conid,
            "period": period,
            "bar": self.TIMEFRAME_MAP[interval],
        }
        
        response = requests.get(
            url, 
            params=params, 
            verify=False,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return self._process_client_portal_data(data)
    
    def _fetch_ib_insync(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[Union[str, datetime]],
        end_date: Optional[Union[str, datetime]],
        days: Optional[int],
        sec_type: str,
        exchange: str,
        currency: str,
        what_to_show: str
    ) -> pd.DataFrame:
        """Fetch using ib_insync library."""
        try:
            from ib_insync import Stock, Forex, Future, Contract, util
        except ImportError:
            raise ImportError(
                "ib_insync library required. Install with: pip install ib_insync"
            )
        
        if not self._connected:
            self.connect()
        
        # Create contract based on security type
        if sec_type == "STK":
            contract = Stock(symbol, exchange, currency)
        elif sec_type == "FX":
            # For forex, symbol format is "EUR.USD" -> base="EUR", quote="USD"
            parts = symbol.split(".")
            if len(parts) == 2:
                contract = Forex(parts[0] + parts[1])
            else:
                contract = Forex(symbol)
        elif sec_type == "FUT":
            contract = Future(symbol, exchange=exchange, currency=currency)
        else:
            contract = Contract(
                symbol=symbol,
                secType=sec_type,
                exchange=exchange,
                currency=currency
            )
        
        # Calculate duration
        if days:
            if days <= 1:
                duration = "1 D"
            elif days <= 7:
                duration = f"{days} D"
            elif days <= 30:
                duration = f"{(days // 7) + 1} W"
            elif days <= 365:
                duration = f"{(days // 30) + 1} M"
            else:
                duration = f"{(days // 365) + 1} Y"
        else:
            duration = self.DURATION_MAP.get(interval, "30 D")
        
        # Handle end date
        if end_date is None:
            end_dt = ""
        elif isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = end_date
        
        # Fetch historical data
        bars = self._ib.reqHistoricalData(
            contract,
            endDateTime=end_dt,
            durationStr=duration,
            barSizeSetting=self.TIMEFRAME_MAP[interval],
            whatToShow=what_to_show,
            useRTH=False,
            formatDate=1
        )
        
        if not bars:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = util.df(bars)
        
        return self._process_ib_insync_data(df)
    
    def _process_client_portal_data(self, data: dict) -> pd.DataFrame:
        """Process Client Portal API response."""
        bars = data.get("data", [])
        
        if not bars:
            return pd.DataFrame()
        
        df = pd.DataFrame(bars)
        
        # Rename columns
        column_map = {
            't': 'Open Time',
            'o': 'Open',
            'h': 'High',
            'l': 'Low',
            'c': 'Close',
            'v': 'Volume'
        }
        
        df = df.rename(columns=column_map)
        
        # Convert timestamp (milliseconds)
        if 'Open Time' in df.columns:
            df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms', utc=True)
        
        # Select columns
        output_cols = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [c for c in output_cols if c in df.columns]
        
        return df[available_cols].reset_index(drop=True)
    
    def _process_ib_insync_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process ib_insync DataFrame."""
        if df.empty:
            return df
        
        # Rename columns to match our format
        column_map = {
            'date': 'Open Time',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'barCount': 'Trades',
            'average': 'VWAP'
        }
        
        df = df.rename(columns=column_map)
        
        # Ensure datetime
        if 'Open Time' in df.columns:
            df['Open Time'] = pd.to_datetime(df['Open Time'], utc=True)
        
        # Select columns
        output_cols = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        if 'Trades' in df.columns:
            output_cols.append('Trades')
        if 'VWAP' in df.columns:
            output_cols.append('VWAP')
        
        available_cols = [c for c in output_cols if c in df.columns]
        
        return df[available_cols].reset_index(drop=True)
    
    def get_positions(self) -> pd.DataFrame:
        """
        Get current positions (ib_insync mode only).
        
        Returns:
            pd.DataFrame: Current positions
        """
        if self.use_client_portal:
            raise NotImplementedError("Use ib_insync mode for positions")
        
        if not self._connected:
            self.connect()
        
        from ib_insync import util
        
        positions = self._ib.positions()
        
        if not positions:
            return pd.DataFrame()
        
        return util.df(positions)
    
    def get_account_summary(self) -> dict:
        """
        Get account summary (ib_insync mode only).
        
        Returns:
            dict: Account summary
        """
        if self.use_client_portal:
            raise NotImplementedError("Use ib_insync mode for account summary")
        
        if not self._connected:
            self.connect()
        
        summary = self._ib.accountSummary()
        
        return {item.tag: item.value for item in summary}
