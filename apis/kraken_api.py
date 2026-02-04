# 2026.02.04  18.00
from fastapi import APIRouter
import requests

router = APIRouter()

@router.get("/check-stocks")
def check_stocks():
    url = "https://api.kraken.com/0/public/Ticker"
    
    # Standardized parameters for xStocks
    params = {
        "pair": "TSLAxUSD,NVDAxUSD,AAPLxUSD,SPYxUSD",
        "asset_class": "tokenized_asset" 
    }
    
    try:
        response = requests.get(url, params=params).json()
        
        if response.get("error"):
            return {"status": "error", "message": response["error"]}

        data = response["result"]
        results = []

        for pair_name, info in data.items():
            current_price = float(info["c"][0])
            
            results.append({
                "ticker": pair_name.replace("XUSD", "x"),
                "price": current_price
            })

        return {"status": "success", "data": results}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
