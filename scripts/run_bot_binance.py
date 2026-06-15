"""
Versión del bot EMA10/EMA50 usando WebSockets para ejecutar órdenes al cierre exacto de la vela.
- Usa Binance Futures USDT-M.
- Par: FARTUSDT
- Temporalidad: 5m
- Señales LONG/SHORT según EMA10 vs EMA50
- Orden de mercado enviada inmediatamente al cierre de la vela.
- Manejo básico de errores y reconexión automática.
"""

import time
import pandas as pd
from binance import ThreadedWebsocketManager, Client
import math
import os

# ---------- CONFIG ----------
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
if not API_KEY or not API_SECRET:
    raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env file")

SYMBOL = 'FARTUSDT'
INTERVAL = '5m'
EMA_SHORT = 1
EMA_LONG = 4
LEVERAGE = 5
PERCENT_ACCOUNT_TO_USE = 0.1  # 100% (ajustar según tolerancia)

# ---------- CLIENTE ----------
client = Client(API_KEY, API_SECRET)
closes = []
last_signal = None

# ---------- FUNCIONES ----------

def get_usdt_balance():
    bals = client.futures_account_balance()
    for b in bals:
        if b['asset'] == 'USDT':
            return float(b['balance'])
    return 0.0


def get_symbol_info(symbol):
    info = client.futures_exchange_info()
    for s in info['symbols']:
        if s['symbol'] == symbol:
            return s
    return None


def get_trade_quantity(usdt_amount, price, symbol_info, leverage):
    raw_qty = (usdt_amount * leverage) / price
    for f in symbol_info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            step = float(f['stepSize'])
            minQty = float(f['minQty'])
            maxQty = float(f['maxQty'])
            adj_qty = math.floor(raw_qty / step) * step
            if adj_qty < minQty:
                raise ValueError(f"Cantidad calculada {adj_qty} menor al mínimo {minQty}")
            if adj_qty > maxQty:
                adj_qty = math.floor(maxQty / step) * step
            return float(round(adj_qty, 8))
    return float(round(raw_qty, 8))


def close_all_positions(symbol):
    try:
        positions = client.futures_position_information(symbol=symbol)
        for pos in positions:
            posAmt = float(pos['positionAmt'])
            if posAmt == 0:
                continue
            side = 'SELL' if posAmt > 0 else 'BUY'
            qty = abs(posAmt)
            print(f"Cerrando posición: {posAmt} -> {side} qty {qty}")
            client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
    except Exception as e:
        print("Error cerrando posiciones:", e)


def place_market_order(symbol, side, qty):
    print(f"Enviando orden MARKET {side} qty={qty} para {symbol}")
    return client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)

# ---------- LÓGICA WEBSOCKET ----------

def handle_socket_message(msg):
    global closes, last_signal
    kline = msg['k']
    is_closed = kline['x']
    close_price = float(kline['c'])

    closes.append(close_price)
    if len(closes) < EMA_LONG:
        return

    df = pd.DataFrame({'close': closes})
    df['EMA_short'] = df['close'].ewm(span=EMA_SHORT, adjust=False).mean()
    df['EMA_long'] = df['close'].ewm(span=EMA_LONG, adjust=False).mean()

    if is_closed:
        ema_s = df['EMA_short'].iloc[-1]
        ema_l = df['EMA_long'].iloc[-1]
        signal = 'LONG' if ema_s > ema_l else 'SHORT'
        print(f"Vela cerrada: {close_price} - EMA10: {ema_s:.2f}, EMA50: {ema_l:.2f} -> {signal}")

        if signal != last_signal:
            close_all_positions(SYMBOL)
            usdt_bal = get_usdt_balance()
            symbol_info = get_symbol_info(SYMBOL)
            qty = get_trade_quantity(usdt_bal * PERCENT_ACCOUNT_TO_USE, close_price, symbol_info, LEVERAGE)
            side = 'BUY' if signal == 'LONG' else 'SELL'
            try:
                place_market_order(SYMBOL, side, qty)
                last_signal = signal
            except Exception as e:
                print("Error al colocar orden:", e)

# ---------- EJECUTAR BOT ----------
try:
    twm = ThreadedWebsocketManager()
    twm.start()
    twm.start_kline_socket(callback=handle_socket_message, symbol=SYMBOL, interval=INTERVAL)
    print("Bot ejecutándose con WebSocket — esperando velas cerradas...")

    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Bot detenido por usuario.")
    twm.stop()