# NSE/BSE Stock Market Analysis Tool

A production-style Python tool for end-to-end stock analysis of Indian equities (NSE/BSE tickers such as `RELIANCE.NS`, `TCS.NS`, `RELIANCE.BO`).

## Features

- **Technical Analysis**
  - RSI (14)
  - MACD (12/26/9)
  - Moving Averages: 20, 50, 200
  - Bollinger Bands (20, 2)
  - Volume analysis (20-day average and volume ratio)
- **Fundamental Snapshot**
  - P/E Ratio
  - EPS
  - Market Cap
  - Debt to Equity
  - Revenue Growth
- **Signal & Market Structure**
  - Buy / Hold / Sell suggestion
  - Bullish / Bearish / Sideways trend classification
  - Support and resistance detection
- **Advanced Metrics**
  - Risk score (0–100)
  - Trend strength (0–100)
  - Annualized volatility
- **Visualization**
  - Plotly interactive dashboard: candlestick + MAs + RSI + MACD
  - Matplotlib static multi-panel chart
- **Scanner**
  - Optional top-stock scanner over a predefined NSE/BSE universe

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install yfinance nsepython pandas numpy matplotlib plotly ta
```

## Usage

### Single stock analysis

```bash
python stock_analysis_tool.py --ticker RELIANCE.NS --timeframe 6mo
```

### With interactive chart

```bash
python stock_analysis_tool.py --ticker TCS.NS --timeframe 1y --plotly
```

### With matplotlib chart

```bash
python stock_analysis_tool.py --ticker INFY.NS --timeframe 1mo --matplotlib
```

### Top stock scanner

```bash
python stock_analysis_tool.py --scan --timeframe 6mo --top-n 5
```

## Notes

- Data is sourced primarily through Yahoo Finance (`yfinance`).
- For intraday/high-frequency, exchange APIs or paid feeds are recommended.
- Scanner is best-effort and may skip symbols if the upstream data source is temporarily unavailable.
