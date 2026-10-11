from pathlib import Path

import pandas as pd

from step1_load import load_mt5_csv

FILE = Path(__file__).parent / "DJIUSD_M5_202502242040_202607291115.csv"


def to_h1(df):
    # Combine every 12 five-minute candles into one hourly candle
    h1 = df.resample("1h").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "tickvol": "sum",
    })
    # Weekend hours have no candles at all, so drop them
    return h1.dropna(subset=["open"])


def add_atr(df, period=14):
    prev_close = df["close"].shift(1)
    # True Range = the biggest of these three distances
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    # ATR = Wilder smoothing of the True Range
    df["tr"] = tr
    df["atr"] = tr.ewm(alpha=1 / period, adjust=False).mean()
    return df


if __name__ == "__main__":
    m5 = load_mt5_csv(FILE)
    h1 = add_atr(to_h1(m5))
    print("H1 candles:", len(h1))
    print(h1.tail(5)[["open", "high", "low", "close", "atr"]])
    print("Average ATR:", round(h1["atr"].mean(), 1))

    out = Path(__file__).parent / "h1_atr.csv"
    h1.to_csv(out)
    print("Saved:", out)
