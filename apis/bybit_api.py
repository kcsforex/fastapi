# 2025.02.18  11.00
import pandas as pd
import ccxt
import ccxt.async_support as ccxt_async
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
import dash
from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from sqlalchemy import create_engine
from pydantic import BaseModel
from typing import List, Optional

# ----- 1. CONFIGURATION -----
DB_CONFIG = "postgresql+psycopg://sql_admin:sql_pass@postgresql:5432/n8n"
sql_engine = create_engine(DB_CONFIG, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=1800,      
    connect_args={'connect_timeout': 5, 'keepalives': 1, 'keepalives_idle': 30, 'keepalives_interval': 10, 'keepalives_count': 5})

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ZEN/USDT", "LTC/USDT", "AVAX/USDT", "LINK/USDT", "HYPE/USDT", "BCH/USDT", "BNB/USDT", "SUI/USDT"]

# ----- 2. FASTAPI/APIRouter -----
router = APIRouter()

bybit = ccxt.bybit() 
bybit_async = ccxt_async.bybit({'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
TIMEFRAME = '5m' 
limit = 101   

class Candle(BaseModel):
    symbol: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    sma100: float
    signal: str

async def fetch_one_symbol(symbol: str, since: Optional[int] = None):
    try:     
        ohlcv = await bybit_async.fetch_ohlcv(symbol, TIMEFRAME, limit=110)     
        if len(ohlcv) < 101: 
            return []
    
        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        df['sma100'] = df['c'].rolling(window=100).mean()
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal = "NON-CROSS"
        if prev['c'] <= prev['sma100'] and curr['c'] > curr['sma100']:
            signal = "BULL-CROSS"
        elif prev['c'] >= prev['sma100'] and curr['c'] < curr['sma100']:
            signal = "BEAR-CROSS"
        
        # Payload Reduction: Only return the latest candle with the signal
        # Returning all 110 candles for 50 assets will crash n8n's memory
        return [{
            "symbol": symbol.replace("/", "-"),
            "timestamp": int(curr['ts']),
            "open": float(curr['o']),
            "high": float(curr['h']),
            "low": float(curr['l']),
            "close": float(curr['c']),
            "volume": float(curr['v']),
            "sma_100": float(curr['sma100']),
            "sma_signal": signal
        }]

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []

@router.get("/fetch-all", response_model=List[Candle])
async def fetch_all_cryptos(since: Optional[int] = Query(None, description="Start timestamp in milliseconds")):

    tasks = [fetch_one_symbol(s, since) for s in SYMBOLS]
    results = await asyncio.gather(*tasks)    
    flattened_results = [candle for symbol_list in results for candle in symbol_list]    
    if not flattened_results:
        return []
        
    return flattened_results

@router.on_event("shutdown")
async def shutdown_event():
    await bybit_async.close()

@router.get("/bybit")
def bybit_data():

    results = []
    timestamp = bybit.milliseconds()
    
    for symbol in SYMBOLS:
        try:
            ohlcv = bybit.fetch_ohlcv(symbol, TIMEFRAME, limit=limit)
            closes = [candle[4] for candle in ohlcv]        
            sma_100 = sum(closes[-100:]) / 100
            current_price = closes[-1]
            curr_status = "ABOVE" if current_price > sma_100 else "BELOW"
            diff_percent = ((current_price - sma_100) / sma_100) * 100
        
            prev_close = closes[-2]
            prev_sma = sum(closes[-101:-1]) / 100  # SMA100 for previous candle
            
            prev_status = "ABOVE" if prev_close > prev_sma else "BELOW"
            
            if prev_status == "BELOW" and curr_status == "ABOVE":
                price_cross = "BULL-CROSS"
            elif prev_status == "ABOVE" and curr_status == "BELOW":
                price_cross = "BEAR-CROSS"
            else:
                price_cross = "NON-CROSS"
            
            coin_name = symbol.split('/')[0]
            results.append({"symbol": coin_name, "pair": symbol, "price": round(current_price, 2), "sma_100": round(sma_100, 2),
                "price_status": curr_status, "price_cross": price_cross, "percent_diff": round(diff_percent, 2), "timestamp": timestamp
            })
            
        except Exception as e:
            coin_name = symbol.split('/')[0]
            results.append({"symbol": coin_name, "pair": symbol, "price": 0, "price_status": "ERROR", "price_cross": "ERROR", 
            "error": str(e), "timestamp": timestamp
            })
                          
    return results
