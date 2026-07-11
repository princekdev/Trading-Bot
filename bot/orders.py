"""
orders.py
---------
Order-level business logic: validates requests, delegates to the API
client, and formats results for display. Keeps the CLI layer thin.
"""

from dataclasses import dataclass
from typing import Optional

from bot.client import BinanceFuturesTestnetClient, BinanceClientError
from bot.logging_config import get_logger, get_order_logger
from bot.validators import validate_order_request, ValidationError

logger = get_logger()


@dataclass
class OrderResult:
    order_id: str
    status: str
    executed_qty: str
    avg_price: str
    raw: dict


class OrderError(Exception):
    """Raised when an order cannot be validated or placed."""


def build_order_summary(symbol: str, side: str, order_type: str, quantity: float, price: Optional[float]) -> str:
    lines = [
        "Order Request Summary",
        "----------------------",
        f"Symbol     : {symbol}",
        f"Side       : {side}",
        f"Order Type : {order_type}",
        f"Quantity   : {quantity}",
    ]
    if order_type == "LIMIT":
        lines.append(f"Price      : {price}")
    return "\n".join(lines)


def place_order(
    client: BinanceFuturesTestnetClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
) -> OrderResult:
    """
    Validate and place an order, returning a normalized OrderResult.

    Raises OrderError for both validation failures and API/network failures,
    so the CLI only needs to catch one exception type.
    """
    try:
        symbol, side, order_type, quantity, price = validate_order_request(
            symbol, side, order_type, quantity, price
        )
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        raise OrderError(str(exc)) from exc

    # From here on the order type is known and valid, so route all
    # request/response/error logging into its dedicated log file
    # (logs/market_order.log or logs/limit_order.log).
    order_logger = get_order_logger(order_type)

    order_logger.info(
        "Placing %s %s order for %s qty=%s price=%s", order_type, side, symbol, quantity, price
    )

    try:
        response = client.place_order(
            symbol=symbol, side=side, order_type=order_type, quantity=quantity, price=price,
            logger=order_logger,
        )
    except BinanceClientError as exc:
        order_logger.error("Order placement failed: %s", exc)
        raise OrderError(str(exc)) from exc

    result = OrderResult(
        order_id=str(response.get("orderId", "N/A")),
        status=str(response.get("status", "UNKNOWN")),
        executed_qty=str(response.get("executedQty", "0")),
        avg_price=str(response.get("avgPrice", "N/A")),
        raw=response,
    )
    order_logger.info("Order placed successfully: %s", result)
    return result
