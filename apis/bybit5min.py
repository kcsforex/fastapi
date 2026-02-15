import asyncio
import ccxt.async_support as ccxt
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Crypto Data Proxy")

# --- CONFIGURATION ---
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"]
TIMEFRAME = '5m'

exchange = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

class Candle(BaseModel):
    symbol: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

async def fetch_one_symbol(symbol: str, since: Optional[int] = None):
    """Fetches OHLCV using 'since' to catch up on missed data."""
    try:
        # If since is None, CCXT/Exchange defaults to most recent candles
        # If since is provided, it fetches candles starting from that timestamp
        ohlcv = await exchange.fetch_ohlcv(symbol, TIMEFRAME, since=since)
        
        return [
            {
                "symbol": symbol.replace("/", "-"),
                "timestamp": c[0],
                "open": c[1],
                "high": c[2],
                "low": c[3],
                "close": c[4],
                "volume": c[5]
            }
            for c in ohlcv
        ]
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []

@app.get("/fetch-all", response_model=List[Candle])
async def fetch_all_cryptos(since: Optional[int] = Query(None, description="Start timestamp in milliseconds")):
    """
    Parallel fetch for all symbols using the 'since' parameter.
    """
    tasks = [fetch_one_symbol(s, since) for s in SYMBOLS]
    results = await asyncio.gather(*tasks)
    
    # Flatten the list of lists
    flattened_results = [candle for symbol_list in results for candle in symbol_list]
    
    if not flattened_results:
        # If it's a routine sync and no NEW candles exist, return empty list
        return []
        
    return flattened_results

@app.on_event("shutdown")
async def shutdown_event():
    await exchange.close()
