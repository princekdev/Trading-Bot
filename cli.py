#!/usr/bin/env python3
"""
cli.py
------
Command-line interface for the Binance Futures (USDT-M) Testnet Trading Bot.

Example usage:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
"""

import argparse
import sys

from bot.client import BinanceFuturesTestnetClient, BinanceClientError
from bot.logging_config import get_logger
from bot.orders import build_order_summary, place_order, OrderError
from bot.validators import ValidationError, validate_order_request

logger = get_logger()


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures (USDT-M) Testnet."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"], help="Order side")
    parser.add_argument(
        "--type", required=True, dest="order_type",
        choices=["MARKET", "LIMIT", "market", "limit"], help="Order type"
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument(
        "--price", required=False, default=None,
        help="Limit price (mandatory for LIMIT orders, must be omitted for MARKET orders)"
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    # Validate inputs up front so a bad request never reaches the network layer.
    try:
        symbol, side, order_type, quantity, price = validate_order_request(
            args.symbol, args.side, args.order_type, args.quantity, args.price
        )
    except ValidationError as exc:
        print(f"Invalid input: {exc}")
        logger.error("CLI input validation failed: %s", exc)
        return 1

    print(build_order_summary(symbol, side, order_type, quantity, price))
    print()

    try:
        client = BinanceFuturesTestnetClient()
    except BinanceClientError as exc:
        print(f"Setup error: {exc}")
        logger.error("Client initialization failed: %s", exc)
        return 1

    try:
        result = place_order(client, symbol, side, order_type, quantity, price)
    except OrderError as exc:
        print(f"Order FAILED: {exc}")
        logger.error("Order failed: %s", exc)
        return 1

    print("Order SUCCESSFUL")
    print("----------------")
    print(f"Order ID     : {result.order_id}")
    print(f"Status       : {result.status}")
    print(f"Executed Qty : {result.executed_qty}")
    print(f"Avg Price    : {result.avg_price}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
