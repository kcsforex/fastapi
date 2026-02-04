# 2026.02.04  18.00
from fastapi import APIRouter
import requests

router = FastAPI()

last_known_prices = {}

@router.get("/check-stocks")
def check_stocks():
    url = "https://api.kraken.com/0/public/Ticker"
    pairs = ["TSLAXUSD", "NVDAXUSD", "AAPLXUSD", "SPYXUSD"]
    params = {"pair": ",".join(pairs), "asset_class": "tokenized_asset"}
    
    try:
        response = requests.get(url, params=params).json()
        if response.get("error"):
            return {"status": "error", "message": response["error"]}

        results = []
        for pair in pairs:
            raw_data = response["result"].get(pair)
            current_price = float(raw_data["c"][0])
            ticker = pair.replace("XUSD", "x")
            
            # Check for a 2% drop logic
            alert = False
            drop_percent = 0
            if ticker in last_known_prices:
                old_price = last_known_prices[ticker]
                drop_percent = ((old_price - current_price) / old_price) * 100
                if drop_percent >= 2.0:
                    alert = True
            
            # Update history
            last_known_prices[ticker] = current_price
            
            results.append({
                "ticker": ticker,
                "price": current_price,
                "alert": alert,
                "drop_percent": round(drop_percent, 2)
            })
            
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Runs the server on localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
