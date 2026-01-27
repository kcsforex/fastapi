# 2025.01.27  18.00
import pandas as pd
import ccxt
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from datetime import datetime
from fastapi import APIRouter
import dash
from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from sqlalchemy import create_engine
import json

# ----- 1. CONFIGURATION -----
DB_CONFIG = "postgresql+psycopg://sql_admin:sql_pass@72.62.151.169:5432/n8n"
sql_engine = create_engine(DB_CONFIG, pool_size=0, max_overflow=0, pool_pre_ping=True)
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ZEN/USDT", "LTC/USDT", "AVAX/USDT", "LINK/USDT", "HYPE/USDT", "BCH/USDT", "BNB/USDT", "AAVE/USDT"]

# ----- 2. FASTAPI  (n8n targets this) -----
router = APIRouter()

@router.get("/newsapi")
async def fetch_news():
    URL = "https://www.cryptocompare.com/news/list/latest/?categories=AAVE"
    browser_cfg = BrowserConfig(browser_type="chromium", headless=True, verbose=False)
    
    run_cfg = CrawlerRunConfig(page_timeout=30000,    wait_until="networkidle", cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=URL, config=run_cfg)
        
        if not result or result.status_code != 200:
            return {"error": f"status {getattr(result, 'status_code', 'unknown')}"}

        soup = BeautifulSoup(result.html or "", "html.parser")

        articles = []
        for a in soup.select("a"):
            href = a.get("href", "")
            if "/news/" in href:
                title = a.get_text(strip=True)
                link = href if href.startswith("http") else f"https://www.cryptocompare.com{href}"
                if title:
                    articles.append({"title": title, "link": link})

        return {"articles": articles}


@router.get("/bybit")
def bybit_data():

    exchange = ccxt.bybit()  
    timeframe = '5m' 
    limit = 101   
    results = []
    timestamp = exchange.milliseconds()
    
    for symbol in SYMBOLS:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
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
