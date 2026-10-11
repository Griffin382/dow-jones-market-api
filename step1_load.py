import pandas as pd
from pathlib import Path

FILE = Path(__file__).parent / "DJIUSD_M5_202502242040_202607291115.csv"


def load_mt5_csv(path):
    # MT5 exports are tab-separated with headers like <DATE>, <TIME>, ...
    df = pd.read_csv(path, sep="\t")
    df.columns = [c.strip("<>").lower() for c in df.columns]

    # Merge date + time into one datetime column and use it as the index
    df["time"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")
    df = df.drop(columns=["date"]).set_index("time").sort_index()
    return df


def check_quality(df):
    print("Rows:", len(df))
    print("From:", df.index.min(), "To:", df.index.max())
    print("Duplicate timestamps:", df.index.duplicated().sum())
    print("Missing values:\n", df.isna().sum()[df.isna().sum() > 0])

    # Basic OHLC sanity: high must be the highest, low the lowest
    bad = df[(df["high"] < df[["open", "close"]].max(axis=1)) |
             (df["low"] > df[["open", "close"]].min(axis=1))]
    print("Bad OHLC rows:", len(bad))

    # Gaps bigger than 5 minutes (weekends and holidays are expected)
    gaps = df.index.to_series().diff()
    big = gaps[gaps > pd.Timedelta(minutes=5)]
    print("Gaps > 5min:", len(big))
    print("Biggest gaps:\n", big.sort_values(ascending=False).head(5))


if __name__ == "__main__":
    df = load_mt5_csv(FILE)
    print(df.head())
    check_quality(df)
