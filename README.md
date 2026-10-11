# Dow Jones Market Data API

A small data pipeline and REST API built with Python, SQLite and FastAPI.
It takes raw 5-minute Dow Jones (US30) candles exported from MetaTrader 5, cleans them, converts them to H1 candles, calculates ATR(14), stores everything in a database and serves it through an API.

## Pipeline

1. `step1_load.py` reads the raw MT5 CSV (tab-separated), cleans the column names, builds a datetime index and checks data quality (duplicates, missing values, invalid OHLC rows, gaps).
2. `step2_atr.py` resamples M5 candles to H1 and calculates True Range and ATR(14) with Wilder smoothing. Output: `h1_atr.csv`.
3. `step3_db.py` stores the H1 candles in a SQLite database (`market.db`) with a primary key and an index, and runs sample SQL queries (GROUP BY by hour and month).
4. `main.py` is a FastAPI app that reads the database and exposes the data as JSON.

## Endpoints

| Endpoint | Description |
| --- | --- |
| `GET /health` | Check that the server is running |
| `GET /candles?limit=10&start=2026-07-01&end=2026-07-02` | H1 candles with ATR, newest first. Returns 404 if no candles match |
| `GET /atr/stats` | Number of candles, average, minimum and maximum ATR |
| `GET /docs` | Interactive API documentation (Swagger UI) |

## How to run

```bash
pip install pandas fastapi uvicorn

# put the raw CSV next to the scripts, then:
python step2_atr.py
python step3_db.py
python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs in your browser.

## Notes

- The raw data covers 2025-02-24 to 2026-07-29. Weekends and holidays have no candles.
- Timestamps use the broker's server time, not local time.
- The raw CSV is not included in this repository.

## Tech

Python, pandas, SQLite (SQL), FastAPI, REST API, Git
