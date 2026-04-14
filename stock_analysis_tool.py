#!/usr/bin/env python3
"""
Stock Market Analysis Tool for NSE/BSE equities.

Features
--------
- Pulls latest market + fundamental data from Yahoo Finance via yfinance.
- Computes technical indicators (RSI, MACD, SMA20/50/200, Bollinger Bands, volume trend).
- Produces buy/hold/sell suggestion and trend classification.
- Estimates support/resistance using recent swing points.
- Computes optional risk score, trend strength, and volatility.
- Generates interactive Plotly chart and optional Matplotlib fallback chart.

Example
-------
python stock_analysis_tool.py --ticker RELIANCE.NS --timeframe 6mo --plotly
python stock_analysis_tool.py --ticker TCS.NS --timeframe 1y --matplotlib
python stock_analysis_tool.py --scan --timeframe 6mo
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Data source(s)
import yfinance as yf

# Technical indicators
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

# Visualization
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots


TIMEFRAME_MAP = {
    "1mo": "1mo",
    "6mo": "6mo",
    "1y": "1y",
    "1yr": "1y",
    "1m": "1mo",
}


@dataclass
class AnalysisResult:
    ticker: str
    suggestion: str
    trend: str
    indicator_values: Dict[str, float]
    support_levels: List[float]
    resistance_levels: List[float]
    fundamentals: Dict[str, Optional[float]]
    risk_score: float
    trend_strength: float
    annualized_volatility: float


class StockAnalyzer:
    """Production-style stock analyzer focused on NSE/BSE tickers."""

    def __init__(self, ticker: str, period: str = "6mo", interval: str = "1d"):
        self.ticker = ticker.upper().strip()
        self.period = TIMEFRAME_MAP.get(period.lower(), period)
        self.interval = interval
        self.df: Optional[pd.DataFrame] = None
        self.info: Dict = {}

    def fetch_data(self) -> pd.DataFrame:
        """Download OHLCV data using yfinance."""
        data = yf.download(self.ticker, period=self.period, interval=self.interval, auto_adjust=True, progress=False)
        if data.empty:
            raise ValueError(f"No price data returned for ticker '{self.ticker}'.")

        # Flatten multi-index columns if returned by yfinance.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]

        required_cols = {"Open", "High", "Low", "Close", "Volume"}
        missing = required_cols - set(data.columns)
        if missing:
            raise ValueError(f"Missing required columns in dataset: {sorted(missing)}")

        self.df = data.copy()
        return self.df

    def fetch_fundamentals(self) -> Dict[str, Optional[float]]:
        """Fetch basic fundamentals from Yahoo Finance metadata."""
        ticker_obj = yf.Ticker(self.ticker)
        info = ticker_obj.info if hasattr(ticker_obj, "info") else {}
        self.info = info or {}

        fundamentals = {
            "pe_ratio": self.info.get("trailingPE"),
            "eps": self.info.get("trailingEps"),
            "market_cap": self.info.get("marketCap"),
            "debt_to_equity": self.info.get("debtToEquity"),
            "revenue_growth": self.info.get("revenueGrowth"),
        }
        return fundamentals

    def compute_indicators(self) -> pd.DataFrame:
        """Compute technical indicators using ta library."""
        if self.df is None:
            raise RuntimeError("Price data not loaded. Call fetch_data() first.")

        df = self.df.copy()

        # Moving averages
        df["SMA_20"] = SMAIndicator(close=df["Close"], window=20).sma_indicator()
        df["SMA_50"] = SMAIndicator(close=df["Close"], window=50).sma_indicator()
        df["SMA_200"] = SMAIndicator(close=df["Close"], window=200).sma_indicator()

        # RSI
        df["RSI_14"] = RSIIndicator(close=df["Close"], window=14).rsi()

        # MACD
        macd = MACD(close=df["Close"], window_slow=26, window_fast=12, window_sign=9)
        df["MACD"] = macd.macd()
        df["MACD_SIGNAL"] = macd.macd_signal()
        df["MACD_HIST"] = macd.macd_diff()

        # Bollinger Bands
        bb = BollingerBands(close=df["Close"], window=20, window_dev=2)
        df["BB_UPPER"] = bb.bollinger_hband()
        df["BB_MIDDLE"] = bb.bollinger_mavg()
        df["BB_LOWER"] = bb.bollinger_lband()

        # Volume analysis
        df["VOL_MA_20"] = df["Volume"].rolling(20).mean()
        df["VOL_RATIO"] = df["Volume"] / df["VOL_MA_20"]

        # Volatility: daily log-return std annualized
        log_ret = np.log(df["Close"] / df["Close"].shift(1))
        df["ANN_VOL"] = log_ret.rolling(20).std() * np.sqrt(252)

        self.df = df
        return df

    def detect_support_resistance(self, lookback: int = 120) -> Tuple[List[float], List[float]]:
        """Simple swing-high/swing-low detection for support and resistance."""
        if self.df is None:
            raise RuntimeError("Indicators not computed. Call compute_indicators() first.")

        df = self.df.tail(lookback).copy()
        highs = df["High"]
        lows = df["Low"]

        swing_high_mask = (highs.shift(1) < highs) & (highs.shift(-1) < highs)
        swing_low_mask = (lows.shift(1) > lows) & (lows.shift(-1) > lows)

        resistance = sorted(highs[swing_high_mask].dropna().tail(5).tolist())
        support = sorted(lows[swing_low_mask].dropna().tail(5).tolist())

        return support, resistance

    def classify_trend(self) -> Tuple[str, float]:
        """Classify trend and derive trend strength from moving average alignment."""
        if self.df is None:
            raise RuntimeError("Indicators not computed. Call compute_indicators() first.")

        row = self.df.dropna().iloc[-1]
        close, ma20, ma50, ma200 = row["Close"], row["SMA_20"], row["SMA_50"], row["SMA_200"]

        if close > ma20 > ma50 > ma200:
            trend = "Bullish"
        elif close < ma20 < ma50 < ma200:
            trend = "Bearish"
        else:
            trend = "Sideways"

        # Normalized trend strength (0-100) based on MA spread.
        ma_spread = abs(ma20 - ma200) / max(close, 1e-9)
        trend_strength = float(np.clip(ma_spread * 800, 0, 100))
        return trend, trend_strength

    def generate_signal(self) -> str:
        """Heuristic Buy/Hold/Sell signal based on multi-indicator confluence."""
        if self.df is None:
            raise RuntimeError("Indicators not computed. Call compute_indicators() first.")

        row = self.df.dropna().iloc[-1]
        score = 0

        # RSI contribution
        if row["RSI_14"] < 30:
            score += 2
        elif row["RSI_14"] > 70:
            score -= 2

        # MACD contribution
        if row["MACD"] > row["MACD_SIGNAL"]:
            score += 1
        else:
            score -= 1

        # Trend + MA contribution
        if row["Close"] > row["SMA_50"]:
            score += 1
        else:
            score -= 1

        if row["Close"] > row["SMA_200"]:
            score += 1
        else:
            score -= 1

        # Bollinger contribution
        if row["Close"] < row["BB_LOWER"]:
            score += 1
        elif row["Close"] > row["BB_UPPER"]:
            score -= 1

        # Volume confirmation
        if row["VOL_RATIO"] > 1.2:
            score += 0.5

        if score >= 2:
            return "Buy"
        if score <= -2:
            return "Sell"
        return "Hold"

    def compute_risk_score(self) -> Tuple[float, float]:
        """Compute risk score (0-100, high means riskier) and annualized volatility."""
        if self.df is None:
            raise RuntimeError("Indicators not computed. Call compute_indicators() first.")

        row = self.df.dropna().iloc[-1]
        vol = float(row["ANN_VOL"]) if not pd.isna(row["ANN_VOL"]) else 0.0
        rsi = float(row["RSI_14"]) if not pd.isna(row["RSI_14"]) else 50.0

        # Combine volatility and RSI extremeness into risk score.
        rsi_extreme = abs(rsi - 50) / 50
        risk_score = np.clip((vol * 130) + (rsi_extreme * 25), 0, 100)
        return float(risk_score), vol

    def run_analysis(self) -> AnalysisResult:
        """End-to-end analysis routine."""
        self.fetch_data()
        fundamentals = self.fetch_fundamentals()
        self.compute_indicators()

        support, resistance = self.detect_support_resistance()
        trend, trend_strength = self.classify_trend()
        suggestion = self.generate_signal()
        risk_score, ann_vol = self.compute_risk_score()

        last = self.df.dropna().iloc[-1]
        indicator_values = {
            "close": float(last["Close"]),
            "rsi_14": float(last["RSI_14"]),
            "macd": float(last["MACD"]),
            "macd_signal": float(last["MACD_SIGNAL"]),
            "sma_20": float(last["SMA_20"]),
            "sma_50": float(last["SMA_50"]),
            "sma_200": float(last["SMA_200"]),
            "bb_upper": float(last["BB_UPPER"]),
            "bb_lower": float(last["BB_LOWER"]),
            "volume": float(last["Volume"]),
            "vol_ratio": float(last["VOL_RATIO"]),
        }

        return AnalysisResult(
            ticker=self.ticker,
            suggestion=suggestion,
            trend=trend,
            indicator_values=indicator_values,
            support_levels=support,
            resistance_levels=resistance,
            fundamentals=fundamentals,
            risk_score=risk_score,
            trend_strength=trend_strength,
            annualized_volatility=ann_vol,
        )

    def plot_plotly(self, title_suffix: str = "") -> None:
        """Interactive chart with candlesticks, MAs, RSI, and MACD."""
        if self.df is None:
            raise RuntimeError("Indicators not computed. Run analysis before plotting.")

        df = self.df.dropna().copy()
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.58, 0.2, 0.22],
            subplot_titles=("Price + Moving Averages", "RSI (14)", "MACD"),
        )

        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Candlestick",
            ),
            row=1,
            col=1,
        )

        for col, name, color in [
            ("SMA_20", "SMA 20", "blue"),
            ("SMA_50", "SMA 50", "orange"),
            ("SMA_200", "SMA 200", "purple"),
        ]:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines", name=name, line=dict(color=color)), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df["BB_UPPER"], mode="lines", name="BB Upper", line=dict(color="gray", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_LOWER"], mode="lines", name="BB Lower", line=dict(color="gray", width=1)), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df["RSI_14"], mode="lines", name="RSI", line=dict(color="green")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="blue", row=2, col=1)

        fig.add_trace(go.Bar(x=df.index, y=df["MACD_HIST"], name="MACD Hist"), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD", line=dict(color="black")), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_SIGNAL"], mode="lines", name="MACD Signal", line=dict(color="red")), row=3, col=1)

        fig.update_layout(
            title=f"{self.ticker} Technical Dashboard {title_suffix}".strip(),
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            height=900,
        )
        fig.show()

    def plot_matplotlib(self) -> None:
        """Simple Matplotlib indicator chart for non-interactive environments."""
        if self.df is None:
            raise RuntimeError("Indicators not computed. Run analysis before plotting.")

        df = self.df.dropna().copy()
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        axes[0].plot(df.index, df["Close"], label="Close", color="black")
        axes[0].plot(df.index, df["SMA_20"], label="SMA 20", color="blue")
        axes[0].plot(df.index, df["SMA_50"], label="SMA 50", color="orange")
        axes[0].plot(df.index, df["SMA_200"], label="SMA 200", color="purple")
        axes[0].fill_between(df.index, df["BB_LOWER"], df["BB_UPPER"], color="gray", alpha=0.15, label="Bollinger Band")
        axes[0].set_title(f"{self.ticker} Price + MAs")
        axes[0].legend(loc="upper left")

        axes[1].plot(df.index, df["RSI_14"], color="green", label="RSI")
        axes[1].axhline(70, linestyle="--", color="red", linewidth=1)
        axes[1].axhline(30, linestyle="--", color="blue", linewidth=1)
        axes[1].set_title("RSI")
        axes[1].legend(loc="upper left")

        axes[2].bar(df.index, df["MACD_HIST"], label="MACD Hist", alpha=0.4)
        axes[2].plot(df.index, df["MACD"], label="MACD", color="black")
        axes[2].plot(df.index, df["MACD_SIGNAL"], label="MACD Signal", color="red")
        axes[2].set_title("MACD")
        axes[2].legend(loc="upper left")

        plt.tight_layout()
        plt.show()


def format_number(value: Optional[float]) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    if abs(value) >= 1e9:
        return f"{value / 1e9:,.2f}B"
    if abs(value) >= 1e6:
        return f"{value / 1e6:,.2f}M"
    if isinstance(value, float):
        return f"{value:,.4f}"
    return str(value)


def print_summary(result: AnalysisResult) -> None:
    """Console output block as requested."""
    iv = result.indicator_values
    f = result.fundamentals

    print("\n" + "=" * 80)
    print(f"STOCK ANALYSIS SUMMARY: {result.ticker}")
    print("=" * 80)

    print("\nTrading Suggestion")
    print(f"- Signal: {result.suggestion}")
    print(f"- Trend: {result.trend}")
    print(f"- Trend Strength (0-100): {result.trend_strength:.2f}")
    print(f"- Risk Score (0-100): {result.risk_score:.2f}")
    print(f"- Annualized Volatility: {result.annualized_volatility:.2%}")

    print("\nSupport & Resistance")
    print(f"- Support Levels: {[round(x, 2) for x in result.support_levels] if result.support_levels else 'N/A'}")
    print(f"- Resistance Levels: {[round(x, 2) for x in result.resistance_levels] if result.resistance_levels else 'N/A'}")

    print("\nIndicator Readings")
    print(f"- Close: {iv['close']:.2f}")
    print(f"- RSI (14): {iv['rsi_14']:.2f}")
    print(f"- MACD / Signal: {iv['macd']:.4f} / {iv['macd_signal']:.4f}")
    print(f"- SMA 20 / 50 / 200: {iv['sma_20']:.2f} / {iv['sma_50']:.2f} / {iv['sma_200']:.2f}")
    print(f"- Bollinger (Upper/Lower): {iv['bb_upper']:.2f} / {iv['bb_lower']:.2f}")
    print(f"- Volume: {iv['volume']:.0f}, Volume Ratio: {iv['vol_ratio']:.2f}")

    print("\nFundamental Snapshot")
    print(f"- P/E Ratio: {format_number(f.get('pe_ratio'))}")
    print(f"- EPS: {format_number(f.get('eps'))}")
    print(f"- Market Cap: {format_number(f.get('market_cap'))}")
    print(f"- Debt to Equity: {format_number(f.get('debt_to_equity'))}")
    rev = f.get("revenue_growth")
    print(f"- Revenue Growth: {format_number(rev * 100) + '%' if rev is not None else 'N/A'}")
    print("=" * 80 + "\n")


def scan_top_stocks(timeframe: str, top_n: int = 5) -> pd.DataFrame:
    """Basic scanner for popular NSE/BSE tickers ranked by momentum-adjusted score."""
    universe = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "SBIN.NS", "ITC.NS", "LT.NS", "HINDUNILVR.NS", "BHARTIARTL.NS",
        "RELIANCE.BO", "TCS.BO", "INFY.BO", "HDFCBANK.BO", "SBIN.BO",
    ]

    rows = []
    for ticker in universe:
        try:
            analyzer = StockAnalyzer(ticker=ticker, period=timeframe)
            result = analyzer.run_analysis()
            iv = result.indicator_values
            momentum = (iv["close"] - iv["sma_50"]) / max(iv["sma_50"], 1e-9)
            score = (momentum * 100) + (result.trend_strength * 0.4) - (result.risk_score * 0.3)
            rows.append(
                {
                    "ticker": ticker,
                    "signal": result.suggestion,
                    "trend": result.trend,
                    "score": round(score, 2),
                    "risk": round(result.risk_score, 2),
                    "rsi": round(iv["rsi_14"], 2),
                }
            )
        except Exception as exc:  # pragma: no cover - best effort scanner
            rows.append({"ticker": ticker, "signal": "ERROR", "trend": "N/A", "score": -999.0, "risk": np.nan, "rsi": np.nan})
            print(f"[WARN] Scanner failed for {ticker}: {exc}", file=sys.stderr)

    df = pd.DataFrame(rows).sort_values("score", ascending=False).head(top_n)
    return df


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NSE/BSE Stock Market Analysis Tool")
    parser.add_argument("--ticker", type=str, help="Stock ticker (e.g., RELIANCE.NS, TCS.NS)")
    parser.add_argument("--timeframe", type=str, default="6mo", choices=["1mo", "6mo", "1y"], help="Analysis timeframe")
    parser.add_argument("--plotly", action="store_true", help="Show interactive Plotly chart")
    parser.add_argument("--matplotlib", action="store_true", help="Show Matplotlib chart")
    parser.add_argument("--scan", action="store_true", help="Run top stock scanner on a predefined universe")
    parser.add_argument("--top-n", type=int, default=5, help="Number of scanner results to print")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.scan:
        scan_df = scan_top_stocks(timeframe=args.timeframe, top_n=args.top_n)
        print("\nTop Stocks (Scanner Output)")
        print(scan_df.to_string(index=False))
        return

    if not args.ticker:
        raise SystemExit("Please provide --ticker (e.g., RELIANCE.NS)")

    analyzer = StockAnalyzer(ticker=args.ticker, period=args.timeframe)
    result = analyzer.run_analysis()
    print_summary(result)

    if args.plotly:
        analyzer.plot_plotly(title_suffix=f"({args.timeframe})")
    if args.matplotlib:
        analyzer.plot_matplotlib()


if __name__ == "__main__":
    main()
