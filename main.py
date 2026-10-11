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
