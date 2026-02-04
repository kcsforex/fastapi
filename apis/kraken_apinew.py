from fastapi import FastAPI
import requests

app = FastAPI()
last_known_prices = {}

@app.get("/check-stocks")
def check_stocks():
    # 2026 Public Ticker Endpoint
    url = "https://api.kraken.com/0/public/Ticker"
    
    # Try the most common 2026 ID. 
    # If this fails, replace 'TSLAXUSD' with the key you found in the link above.
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
