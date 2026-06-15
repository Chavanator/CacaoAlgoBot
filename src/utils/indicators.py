import numpy as np
import pandas as pd


def calculate_sma(data, period):
    return data['close'].rolling(window=period).mean()


def calculate_ema(data, period):
    return data['close'].ewm(span=period, adjust=False).mean()


def calculate_atr(highs, lows, closes, period=14):
    tr_list = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        tr_list.append(tr)
    atr = np.mean(tr_list[-period:])
    return atr


def calculate_bollinger_bands(data, period=20, std_dev=2.0):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band


def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_ssl_channel(data, period=10):
    sma_high = data['high'].rolling(window=period).mean()
    sma_low = data['low'].rolling(window=period).mean()
    hlv = np.where(data['close'] > sma_high, 1, -1)
    ssl_down = np.where(hlv < 0, sma_high, sma_low)
    ssl_up = np.where(hlv < 0, sma_low, sma_high)
    return ssl_down, ssl_up, hlv


def calculate_awesome_oscillator(data, short_period=5, long_period=34):
    median_price = (data['high'] + data['low']) / 2
    ao = median_price.rolling(window=short_period).mean() - median_price.rolling(window=long_period).mean()
    return ao


def identify_candle_color(candle):
    if candle['open'] < candle['close']:
        return 'Green'
    elif candle['open'] > candle['close']:
        return 'Red'
    else:
        return 'Doji'
