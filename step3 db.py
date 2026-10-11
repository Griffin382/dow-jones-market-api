import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
CSV = BASE / "h1_atr.csv"
DB = BASE / "market.db"


def build_db():
    df = pd.read_csv(CSV, parse_dates=["time"])
    df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB)
    conn.execute("DROP TABLE IF EXISTS candles_h1")
    conn.execute("""
        CREATE TABLE candles_h1 (
            time    TEXT PRIMARY KEY,
            open    REAL NOT NULL,
            high    REAL NOT NULL,
            low     REAL NOT NULL,
            close   REAL NOT NULL,
            tickvol INTEGER,
            tr      REAL,
            atr     REAL
        )
    """)
    df.to_sql("candles_h1", conn, if_exists="append", index=False)
    conn.execute("CREATE INDEX idx_atr ON candles_h1(atr)")
    conn.commit()
    return conn


def run(conn, title, sql):
    print("\n==", title)
    for row in conn.execute(sql):
        print(row)


if __name__ == "__main__":
    conn = build_db()

    run(conn, "Row count",
        "SELECT COUNT(*) FROM candles_h1")

    run(conn, "Last 3 candles",
        "SELECT time, close, atr FROM candles_h1 ORDER BY time DESC LIMIT 3")

    run(conn, "Average ATR by hour of day (top 5 most volatile)",
        """SELECT substr(time, 12, 2) AS hour, ROUND(AVG(atr), 1) AS avg_atr
           FROM candles_h1
           GROUP BY hour
           ORDER BY avg_atr DESC
           LIMIT 5""")

    run(conn, "Average ATR by month",
        """SELECT substr(time, 1, 7) AS month, ROUND(AVG(atr), 1) AS avg_atr
           FROM candles_h1
           GROUP BY month
           ORDER BY month""")

    run(conn, "Candles where ATR is above 200",
        "SELECT COUNT(*) FROM candles_h1 WHERE atr > 200")

    conn.close()
