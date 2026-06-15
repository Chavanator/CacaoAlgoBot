# Cacao_QuantBot

> Multi-broker algorithmic trading framework with 6 strategies combining technical analysis and machine learning. Backtested across 22 forex pairs on IQ Option, Binance Futures, and Phemex.

*"Cacao was used as currency in Mesoamerica. This bot transforms raw market data into digital value."*

## Features

- **6 Trading Strategies**: MHI (3-candle pattern), Torres Gemeas (Twin Towers), EMA Crossover, SSL + Awesome Oscillator, EMA + Bollinger Bands
- **Machine Learning Models**: LSTM, RNN, Linear Regression for price prediction
- **Multi-Broker**: IQ Option (binary/digital options), Binance Futures, Phemex (via TradingView alerts)
- **Risk Management**: Martingale (configurable levels), Stop Win/Loss, Progressive position sizing (Soros)
- **Backtesting Engine**: Systematic testing across 22 forex pairs × 4 timeframes
- **Pair Ranking**: Automatic cataloguer that evaluates and ranks all available pairs

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.9-blue) ![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange) ![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-yellow) ![License](https://img.shields.io/badge/License-MIT-green)

- **Languages**: Python 3.9
- **ML/DL**: TensorFlow / Keras, scikit-learn
- **Data**: pandas, numpy
- **Brokers**: IQ Option API, Binance Futures API, Phemex (TradingView)
- **Indicators**: EMA, SMA, TEMA, Bollinger Bands, ATR, Awesome Oscillator, SSL Channel

## Quick Start

### Prerequisites

- Python 3.9+
- IQ Option account (for IQ Option strategies)
- Binance API keys (for Binance Futures strategies)

### Installation

```bash
git clone https://github.com/yourusername/Cacao_QuantBot.git
cd Cacao_QuantBot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Fill in your credentials in `.env`:
```env
IQ_EMAIL=your_email@example.com
IQ_PASSWORD=your_password
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
```

### Run a Bot

```bash
# IQ Option bot with MHI strategy
python scripts/run_bot_iqoption.py

# Binance Futures EMA crossover bot
python scripts/run_bot_binance.py

# Catalog and rank available pairs
python scripts/catalog_pairs.py

# Download historical data
python scripts/download_historical_data.py
```

## Strategies

| Strategy | Type | Timeframe | Broker |
|---|---|---|---|
| MHI (3-candle pattern) | Technical | 1m/5m | IQ Option |
| Torres Gemeas (Twin Towers) | Technical | 1m | IQ Option |
| EMA Crossover | Trend Following | 5m | Binance Futures |
| EMA + Bollinger Bands | Mean Reversion | 5m | IQ Option |
| SSL + Awesome Oscillator | Momentum | 5m | IQ Option |
| ML Predictors (LSTM/RNN/LR) | Machine Learning | 5m-10m | IQ Option |

## Backtest Results (Highlights)

| Strategy | Asset | Timeframe | Profit Factor | Win Rate | Trades |
|---|---|---|---|---|---|
| OCC Strategy | FARTCOINUSDT | 30m | 12.42 | 78.51% | 684 |
| EMA+BB Optimized | NZDUSD | 5m | - | 100% (73 windows) | - |
| MA Cross (1,27) | Various | 1m | - | 60.98% | - |
| MHI | NZDUSD | 5m | - | 56.39% | 509 |
| MHI | EURJPY | 1m | - | 56.19% | 315 |

## Project Structure

```
Cacao_QuantBot/
├── src/
│   ├── brokers/          # Broker connection clients
│   ├── strategies/       # Trading strategy implementations
│   ├── ml_models/        # ML model architectures
│   ├── risk/             # Risk management modules
│   └── utils/            # Utilities (indicators, config, logging)
├── scripts/              # Standalone executable scripts
├── backtesting/          # Backtest results and reports
├── notebooks/            # Jupyter analysis notebooks
├── data/                 # Market data samples
└── docs/                 # Documentation
```

## Machine Learning Models

- **LSTM**: Sequential model with 2 LSTM layers (50 units each) + Dense layer, trained on 100-candle windows
- **RNN**: SimpleRNN (50 units) with sigmoid output for binary classification (up/down)
- **Linear Regression**: Multi-timeframe (1m/5m/10m) combined signal with ATR filtering

## Risk Management

- **Martingale**: Up to 2 levels with configurable multiplier (default 2x)
- **Soros**: Progressive position sizing based on consecutive wins
- **Stop Win/Loss**: Automatic session termination at configurable thresholds

## License

Distributed under the MIT License. See `LICENSE` for more information.
