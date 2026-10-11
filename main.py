import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

DB = Path(__file__).parent / "market.db"

app = FastAPI(title="Dow Jones Market Data API")


def query(sql, params=()):
    # Open a connection per request, read the rows, then close it
    if not DB.exists():
        raise HTTPException(status_code=500, detail="market.db not found. Run step3_db.py first.")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/candles")
def get_candles(
    limit: int = Query(10, ge=1, le=1000),
    start: Optional[str] = None,  # example: 2026-07-01
    end: Optional[str] = None,    # example: 2026-07-15
):
    sql = "SELECT time, open, high, low, close, atr FROM candles_h1 WHERE 1=1"
    params = []
    if start:
        sql += " AND time >= ?"
        params.append(start)
    if end:
        sql += " AND time <= ?"
        params.append(end + " 23:59:59")
    sql += " ORDER BY time DESC LIMIT ?"
    params.append(limit)

    rows = query(sql, params)
    if not rows:
        raise HTTPException(status_code=404, detail="No candles found for this range")
    return rows


@app.get("/atr/stats")
def atr_stats():
    rows = query("""
        SELECT COUNT(*) AS candles,
               ROUND(AVG(atr), 1) AS avg_atr,
               ROUND(MIN(atr), 1) AS min_atr,
               ROUND(MAX(atr), 1) AS max_atr
        FROM candles_h1
    """)
    return rows[0]


@app.get("/stats/open-both-sides")
def open_both_sides(multiplier: float = Query(0.25, ge=0, le=3)):
    # For each H1 candle: up = how far price went above the open,
    # down = how far it went below the open.
    # LAG(atr) gives the ATR of the PREVIOUS candle, which was already known
    # when this candle opened (so we do not peek into the future).
    rows = query("""
        SELECT COUNT(*) AS candles,
               SUM(CASE WHEN up > ? * atr_prev AND down > ? * atr_prev
                        THEN 1 ELSE 0 END) AS both_sides
        FROM (
            SELECT high - open AS up,
                   open - low AS down,
                   LAG(atr) OVER (ORDER BY time) AS atr_prev
            FROM candles_h1
        )
        WHERE atr_prev IS NOT NULL
    """, (multiplier, multiplier))
    r = rows[0]
    return {
        "multiplier": multiplier,
        "candles": r["candles"],
        "both_sides": r["both_sides"],
        "percent": round(100 * r["both_sides"] / r["candles"], 1),
    }
