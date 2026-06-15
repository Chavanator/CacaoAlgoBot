import os
from dotenv import load_dotenv

load_dotenv()


def get_iq_option_credentials():
    email = os.getenv('IQ_EMAIL', '')
    password = os.getenv('IQ_PASSWORD', '')
    if not email or not password:
        raise ValueError("IQ_EMAIL and IQ_PASSWORD must be set in .env file")
    return email, password


def get_binance_credentials():
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    if not api_key or not api_secret:
        raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env file")
    return api_key, api_secret


def get_trade_settings():
    return {
        'amount': float(os.getenv('DEFAULT_TRADE_AMOUNT', '5')),
        'stop_win': float(os.getenv('DEFAULT_STOP_WIN', '100')),
        'stop_loss': float(os.getenv('DEFAULT_STOP_LOSS', '100')),
        'martingale_levels': int(os.getenv('MARTINGALE_LEVELS', '2')),
        'martingale_factor': float(os.getenv('MARTINGALE_FACTOR', '2.0')),
        'use_martingale': os.getenv('USE_MARTINGALE', 'S').upper() == 'S',
        'account_type': os.getenv('ACCOUNT_TYPE', 'PRACTICE'),
    }
