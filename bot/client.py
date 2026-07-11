"""
client.py
---------
Thin wrapper around the Binance Futures (USDT-M) Testnet REST API.

Uses the `python-binance` client, pointed at the Futures Testnet base URL
(https://testnet.binancefuture.com). Isolated in its own module so the rest
of the application never talks to `python-binance` directly.
"""

import os
from typing import Optional

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests.exceptions import RequestException

from bot.logging_config import get_logger

logger = get_logger()

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised for any failure talking to the Binance Futures Testnet API."""


class BinanceFuturesTestnetClient:
    """
    Wraps python-binance's Client, configured for USDT-M Futures Testnet.

    API credentials are read from the environment (or passed explicitly),
    never hard-coded, and never logged.
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise BinanceClientError(
                "Missing API credentials. Set BINANCE_API_KEY and BINANCE_API_SECRET "
                "environment variables (see README.md)."
            )

        try:
            self._client = Client(self.api_key, self.api_secret, testnet=True)
            # Ensure futures endpoints hit the Futures Testnet, not the spot testnet.
            self._client.FUTURES_URL = FUTURES_TESTNET_BASE_URL + "/fapi"
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to initialize Binance client: %s", exc)
            raise BinanceClientError(f"Failed to initialize Binance client: {exc}") from exc

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        logger=logger,
    ) -> dict:
        """
        Submit an order to Binance USDT-M Futures Testnet.

        `logger` defaults to the general logger but callers (e.g. orders.py)
        may pass an order-type-specific logger so the request/response/error
        trail lands in the matching log file (market_order.log / limit_order.log).

        Raises BinanceClientError on any API, request, or network failure.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        logger.info("Submitting futures order request: %s", params)

        try:
            response = self._client.futures_create_order(**params)
            logger.info("Order response received: %s", response)
            return response
        except BinanceAPIException as exc:
            logger.error("Binance API error (code=%s): %s", exc.code, exc.message)
            raise BinanceClientError(f"Binance API error: {exc.message} (code={exc.code})") from exc
        except BinanceRequestException as exc:
            logger.error("Binance request error: %s", exc)
            raise BinanceClientError(f"Binance request error: {exc}") from exc
        except RequestException as exc:
            logger.error("Network error while contacting Binance: %s", exc)
            raise BinanceClientError(f"Network error while contacting Binance: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive catch-all
            logger.error("Unexpected error placing order: %s", exc)
            raise BinanceClientError(f"Unexpected error placing order: {exc}") from exc

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """Fetch the current status of a previously placed order."""
        try:
            response = self._client.futures_get_order(symbol=symbol, orderId=order_id)
            logger.info("Order status fetched: %s", response)
            return response
        except (BinanceAPIException, BinanceRequestException, RequestException) as exc:
            logger.error("Error fetching order status: %s", exc)
            raise BinanceClientError(f"Error fetching order status: {exc}") from exc
