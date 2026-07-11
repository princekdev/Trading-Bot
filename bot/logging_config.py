"""
logging_config.py
------------------
Centralized logging setup for the trading bot.

Two things are logged:
1. General/CLI-level messages (input validation, setup errors) go to the
   console only, since they happen before an order type is even known.
2. Order-specific requests, responses, and errors are written to a
   dedicated rotating log file per order type, so a MARKET order's trail
   and a LIMIT order's trail are always kept separate and easy to audit:

       logs/market_order.log
       logs/limit_order.log
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

_BASE_LOGGER_NAME = "trading_bot"
_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_console_configured = False
_order_loggers = {}


def _console_handler(level: int) -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setFormatter(_FORMATTER)
    handler.setLevel(level)
    return handler


def get_logger(level: int = logging.INFO) -> logging.Logger:
    """
    General-purpose logger for CLI/setup messages that occur before an
    order type is known (e.g. argument validation, credential errors).
    Logs to console only.
    """
    global _console_configured
    logger = logging.getLogger(_BASE_LOGGER_NAME)
    logger.setLevel(level)

    if not _console_configured:
        logger.addHandler(_console_handler(level))
        logger.propagate = False
        _console_configured = True

    return logger


def get_order_logger(order_type: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a logger dedicated to a single order type ("MARKET" or "LIMIT").

    Each order type gets its own rotating log file:
        logs/market_order.log
        logs/limit_order.log

    so a reviewer can open one file and see exactly (and only) that order
    type's request/response/error trail.
    """
    order_type = order_type.strip().upper()
    logger_name = f"{_BASE_LOGGER_NAME}.{order_type.lower()}_order"

    if logger_name in _order_loggers:
        return _order_loggers[logger_name]

    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"{order_type.lower()}_order.log")

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(_FORMATTER)
    file_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(_console_handler(level))
    logger.propagate = False

    _order_loggers[logger_name] = logger
    return logger
