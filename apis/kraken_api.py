# 2026.02.04  18.00
from fastapi import APIRouter
import requests

router = APIRouter()
last_known_prices = {}

@router.get("/check-stocks")
def check_stocks():
    # 2026 Public Ticker Endpoint
    url = "https://api.kraken.com/0/public/Ticker"
    params = {
        "pair": "TSLAXUSD,NVDAXUSD,AAPLXUSD,SPYXUSD",
        "aclass_base": "tokenized_asset" 
    }
    
    try:
        response = requests.get(url, params=params).json()
        
        if response.get("error"):
            # If it still fails, the pair name is slightly different in your region
            return {"status": "error", "message": response["error"]}

        data = response["result"]
        results = []

        for pair_name, info in data.items():
            current_price = float(info["c"][0])
            
            # Logic for 2% drop alert
            alert = False
            if pair_name in last_known_prices:
                change = ((last_known_prices[pair_name] - current_price) / last_known_prices[pair_name]) * 100
                if change >= 2.0:
                    alert = True
            
            last_known_prices[pair_name] = current_price
            results.append({
                "ticker": pair_name,
                "price": current_price,
                "alert": alert
            })

        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
