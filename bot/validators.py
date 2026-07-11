"""
validators.py
--------------
Pure input-validation helpers for the trading bot CLI.

Kept free of any network / API calls so they can be unit-tested in
isolation and reused by both the CLI layer and the order layer.
"""

import re
from typing import Optional


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Basic USDT-M futures symbol pattern, e.g. BTCUSDT, ETHUSDT, DOGEUSDT
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,17}USDT$")


def validate_symbol(symbol: str) -> str:
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string.")
    symbol = symbol.strip().upper()
    if not _SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected a USDT-M futures pair, e.g. BTCUSDT."
        )
    return symbol


def validate_side(side: str) -> str:
    if not side or not isinstance(side, str):
        raise ValidationError("Side must be a non-empty string.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type must be a non-empty string.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be numeric, got '{quantity}'.")
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0.")
    return quantity


def validate_price(price, order_type: str) -> Optional[float]:
    """
    Price is mandatory for LIMIT orders and ignored (must be None) for MARKET orders.
    """
    order_type = order_type.strip().upper()
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is mandatory for LIMIT orders.")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be numeric, got '{price}'.")
        if price <= 0:
            raise ValidationError("Price must be greater than 0.")
        return price

    # MARKET order: price should not be supplied
    if price is not None:
        raise ValidationError("Price must not be supplied for MARKET orders.")
    return None


def validate_order_request(symbol: str, side: str, order_type: str, quantity, price=None):
    """
    Validate a full order request in one call.
    Returns a tuple of normalized (symbol, side, order_type, quantity, price).
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)
    return symbol, side, order_type, quantity, price
