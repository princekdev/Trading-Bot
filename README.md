# Binance Futures (USDT-M) Testnet Trading Bot

A small, production-style CLI application for placing **MARKET** and **LIMIT**
orders on the Binance Futures **USDT-M Testnet** (`https://testnet.binancefuture.com`).

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py           # Binance API client wrapper (Futures Testnet)
│   ├── orders.py           # Order validation + placement logic
│   ├── validators.py       # Pure input validation helpers
│   └── logging_config.py   # Central logging setup
├── cli.py                  # Argparse CLI entry point
├── logs/
│   ├── market_order.log    # Sample log: one successful MARKET order
│   └── limit_order.log     # Sample log: one successful LIMIT order
├── README.md
└── requirements.txt
```

## 1. Setup

### 1.1 Requirements
- Python 3.9+
- A free Binance Futures Testnet account: https://testnet.binancefuture.com

### 1.2 Install dependencies
```bash
cd trading_bot
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. API Key Configuration

1. Log in to Binance Futures Testnet account and create API credentials from API Management.
2. Go to the API Key section and generate a **Testnet** API key/secret pair.
3. Export the credentials as environment variables (never hard-code them):

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

On Windows (PowerShell):
```powershell
$env:BINANCE_API_KEY="your_testnet_api_key"
$env:BINANCE_API_SECRET="your_testnet_api_secret"
```

The bot reads credentials only from the environment (`bot/client.py`), so no
secrets are ever committed to source control or written to logs.

## 3. Running the Bot

From the `trading_bot/` directory:

### Place a MARKET order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order
```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 3200.50
```

### CLI Arguments
| Argument     | Required          | Description                             |
|--------------|-------------------|------------------------------------------|
| `--symbol`   | Yes               | USDT-M futures pair, e.g. `BTCUSDT`      |
| `--side`     | Yes               | `BUY` or `SELL`                          |
| `--type`     | Yes               | `MARKET` or `LIMIT`                      |
| `--quantity` | Yes               | Order quantity (positive number)         |
| `--price`    | Only for `LIMIT`  | Limit price (must be omitted for MARKET) |

### Example output — MARKET order
```bash
$ python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```
```
Order Request Summary
----------------------
Symbol     : BTCUSDT
Side       : BUY
Order Type : MARKET
Quantity   : 0.01

Order SUCCESSFUL
----------------
Order ID     : 3345671201
Status       : NEW
Executed Qty : 0.0000
Avg Price    : N/A
```

### Example output — LIMIT order
```bash
$ python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 3200.50
```
```
Order Request Summary
----------------------
Symbol     : ETHUSDT
Side       : SELL
Order Type : LIMIT
Quantity   : 0.5
Price      : 3200.5

Order SUCCESSFUL
----------------
Order ID     : 3345678899
Status       : NEW
Executed Qty : 0.0000
Avg Price    : N/A
```

On failure (validation, API, or network error) the CLI prints a clear
`Order FAILED: <reason>` message and exits with a non-zero status code.

## 4. Error Handling

All three failure categories are handled explicitly and logged:
- **Invalid input** → caught by `bot/validators.py`, raised as `ValidationError`,
  surfaced to the CLI before any network call is made.
- **Binance API errors** (e.g. insufficient balance, bad symbol, rate limits)
  → caught around `futures_create_order` in `bot/client.py` as `BinanceAPIException`.
- **Network failures** (timeouts, DNS, connection errors) → caught as
  `requests.exceptions.RequestException` in `bot/client.py`.

All of the above are wrapped into a single `OrderError` at the CLI boundary so
the CLI layer only needs one `except` clause, while the underlying cause is
still fully logged.

## 5. Logging

Every order's request, response, and any error is logged to **its own file**,
in addition to the console, via `bot/logging_config.py`:

- `logs/market_order.log` — request/response trail for every MARKET order
- `logs/limit_order.log`  — request/response trail for every LIMIT order

Each file is a rotating log (5MB x 3 backups). Splitting by order type means
a reviewer can open exactly one file and see only that order type's activity
instead of scanning a single merged log. Input-validation and setup errors
that occur *before* an order type is confirmed (e.g. a bad `--side` value)
are printed to the console only, since there is no order-type file to route
them into yet.

Each log line includes a timestamp, level, logger name, and message — the
outgoing order parameters and the raw Binance response — so every order can
be audited after the fact.

### Sample Logs & Verification Note

This submission includes:

- `logs/market_order.log` — successful **MARKET BUY** order for `BTCUSDT` with the Binance Futures Testnet response (`orderId`, `status`, `executedQty`, and other order details).
- `logs/limit_order.log` — successful **LIMIT BUY** order for `BTCUSDT` at price `50000` with the Binance Futures Testnet response (`orderId`, `status`, `executedQty`, and other order details).

Both log files were generated by running the actual application flow:

`bot/validators.py` → `bot/orders.py` → `bot/client.py` → Binance Futures Testnet API

The orders were executed successfully on Binance Futures Testnet using valid Testnet API credentials. The generated logs contain the actual order request parameters and the response details returned by Binance, including order ID, status, executed quantity, and other order information.

The logs can be used to verify the complete order lifecycle from input validation to API request submission and Binance response handling.

## 6. Assumptions

- The bot targets **USDT-M Futures** only (not Coin-M or Spot).
- Symbol validation assumes standard USDT-M pairs of the form `<BASE>USDT`
  (e.g. `BTCUSDT`, `ETHUSDT`).
- LIMIT orders are submitted with `timeInForce=GTC` (Good-Til-Cancelled),
  which is the most common default for USDT-M futures.
- Exchange-specific constraints (minimum quantity, tick size, notional
  minimums, leverage/margin mode) are enforced by Binance itself; the bot
  performs generic sanity checks (positive numbers, required fields) but
  does not duplicate Binance's exchange-info rules.
- API credentials are supplied via environment variables and are assumed to
  belong to a Testnet account; the client is hard-wired to
  `https://testnet.binancefuture.com` and should not be pointed at
  production without a deliberate code change.
- `python-binance`'s built-in `testnet=True` flag combined with an explicit
  override of `FUTURES_URL` is used to guarantee Futures Testnet (rather
  than Spot Testnet) endpoints are used for all order calls.
- Order status values (e.g. `FILLED` for MARKET, `NEW` or `FILLED` for
  LIMIT) come directly from Binance's response and are displayed as-is,
  rather than the bot inferring or re-deriving fill state itself.
- Only a single order per CLI invocation is supported (no batch/bulk order
  placement), matching the scope of this task.
- The sample logs included in this submission were generated by executing
  the bot with valid Binance Futures Testnet API credentials. The logs
  contain the actual order request parameters and responses returned by
  Binance Futures Testnet.

## 7. Dependencies

See `requirements.txt`:
- `python-binance` — Binance REST API client
- `requests` — HTTP layer / exception types used for network-error handling
