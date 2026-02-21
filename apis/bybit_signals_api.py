# 2025.02.21  11.00
import ccxt
import psycopg
from sqlalchemy import create_engine
import numpy as np
from fastapi import FastAPI, APIRouter, HTTPException, Query
from datetime import datetime

#app = FastAPI(title="Crypto Signal API")
router = APIRouter()


# =========================
# CONFIG
# =========================
DB_CONFIG0 = {
    "host": "localhost",
    "database": "crypto",
    "user": "postgres",
    "password": "password"
} # psycopg.connect(**DB_CONFIG)

DB_CONFIG = "postgresql+psycopg://sql_admin:sql_pass@postgresql:5432/n8n"
sql_engine = create_engine(DB_CONFIG, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=1800,      
    connect_args={'connect_timeout': 5, 'keepalives': 1, 'keepalives_idle': 30, 'keepalives_interval': 10, 'keepalives_count': 5})

SCORE_THRESHOLD = 70


# =========================
# DB HELPERS
# =========================
def get_connection():
    return psycopg.connect(DB_CONFIG)


def get_persistence(symbol, conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM (
                SELECT symbol
                FROM signals
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 3
            ) sub;
        """, (symbol,))
        result = cur.fetchone()
        return result[0] if result else 0


def insert_signal(conn, data):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO signals (symbol, timestamp, change_pct, volume, price, score)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data["symbol"],
            datetime.utcnow(),
            data["change_pct"],
            data["volume"],
            data["price"],
            data["score"]
        ))
    conn.commit()


# =========================
# SCORING FUNCTIONS
# =========================
def momentum_score(change_pct):
    if change_pct < 5:
        return 20
    elif 5 <= change_pct <= 15:
        return 100
    elif 15 < change_pct <= 25:
        return 70
    else:
        return 40


def volume_score(volume, avg_volume):
    if avg_volume == 0:
        return 50

    ratio = volume / avg_volume

    if ratio < 1:
        return 30
    elif 1 <= ratio <= 2:
        return 70
    elif 2 < ratio <= 5:
        return 100
    else:
        return 80


def volatility_score(high, low, price):
    if not high or not low or not price:
        return 50

    range_pct = (high - low) / price * 100

    if range_pct < 2:
        return 30
    elif 2 <= range_pct <= 6:
        return 100
    elif 6 < range_pct <= 12:
        return 70
    else:
        return 40


def persistence_score(appearances):
    if appearances == 1:
        return 40
    elif appearances == 2:
        return 80
    elif appearances >= 3:
        return 100
    return 20


def leverage_score(market):
    max_lev = (
        market.get("limits", {})
        .get("leverage", {})
        .get("max", 0)
    )

    if max_lev >= 50:
        return 100
    elif max_lev >= 25:
        return 80
    elif max_lev >= 10:
        return 60
    else:
        return 30


def final_score(data, avg_volume, appearances, market):
    m = momentum_score(data["change_pct"])
    v = volume_score(data["volume"], avg_volume)
    vol = volatility_score(data["high"], data["low"], data["price"])
    p = persistence_score(appearances)
    l = leverage_score(market)

    score = (
        m * 0.25 +
        v * 0.25 +
        vol * 0.15 +
        p * 0.20 +
        l * 0.15
    )

    return round(score, 2)


# =========================
# CORE ENGINE
# =========================
def generate_signals():
    exchange = ccxt.bybit({
        'enableRateLimit': True,
        'options': {'defaultType': 'linear'}
    })

    markets = exchange.load_markets()
    tickers = exchange.fetch_tickers(params={'category': 'linear'})

    volumes = [
        t.get("quoteVolume", 0)
        for t in tickers.values()
        if t.get("quoteVolume")
    ]
    avg_volume = np.mean(volumes) if volumes else 0

    conn = get_connection()
    results = []

    for symbol, ticker in tickers.items():
        if "/USDT" not in symbol:
            continue

        data = {
            "symbol": symbol,
            "price": ticker.get("last"),
            "change_pct": ticker.get("percentage", 0),
            "volume": ticker.get("quoteVolume", 0),
            "high": ticker.get("high"),
            "low": ticker.get("low"),
        }

        if not data["price"] or not data["volume"]:
            continue

        appearances = get_persistence(symbol, conn)
        market = markets.get(symbol, {})

        score = final_score(data, avg_volume, appearances, market)
        data["score"] = score

        insert_signal(conn, data)

        if score >= SCORE_THRESHOLD:
            results.append(data)

    conn.close()

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results

@router.get("/signals")
def get_signals():
    results = generate_signals()
    return {
        "timestamp": datetime.utcnow(),
        "count": len(results),
        "signals": results
    }
