from fastapi import FastAPI
import ccxt
import pandas as pd

app = FastAPI()
exchange = ccxt.bybit()

@app.get("/analyze/batch")
def analyze_batch():
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    results = []
    
    for symbol in symbols:
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=110)
            df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['sma100'] = df['close'].rolling(window=100).mean()
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            results.append({
                "symbol": symbol,
                "price": float(curr['c']),
                "sma100": float(curr['sma100']),
                "cross_up": bool(prev['c'] <= prev['sma100'] and curr['c'] > curr['sma100']),
                "cross_dn": bool(prev['c'] >= prev['sma100'] and curr['c'] < curr['sma100']),
                "status": "ABOVE" if curr['c'] > curr['sma100'] else "BELOW"
            })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})
            
    return results #Returns a list of dicts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
