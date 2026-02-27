# 2026.02.27  18.00
from fastapi import APIRouter
import requests
from functools import lru_cache

xstocks_list = [
    'AAPLxUSD', 'ABBVxUSD', 'ABTxUSD', 'ACNxUSD', 'AMBRxUSD', 'AMDxUSD', 'AMZNxUSD', 'APPxUSD', 'AVGOxUSD', 'AZNxUSD',
    'BACxUSD', 'BMNRxUSD', 'BTBTxUSD', 'BTGOxUSD', 'CMCSAxUSD', 'COINxUSD', 'COPXxUSD', 'CRCLxUSD', 'CRMxUSD', 
    'CRWDxUSD', 'CSCOxUSD', 'CVXxUSD', 'DFDVxUSD', 'DHRxUSD', 'GLDxUSD', 'GMExUSD', 'GOOGLxUSD', 'GSxUSD', 'HONxUSD', 
    'HOODxUSD', 'IBMxUSD', 'IEMGxUSD', 'IJRxUSD', 'INTCxUSD', 'IWMxUSD', 'JNJxUSD', 'JPMxUSD', 'KOxUSD', 'KRAQxUSD', 
    'LINxUSD', 'LLYxUSD', 'MCDxUSD', 'MDTxUSD', 'METAxUSD', 'MRKxUSD', 'MRVLxUSD', 'MSFTxUSD', 'MSTRxUSD', 'NFLXxUSD', 
    'NVDAxUSD', 'NVOxUSD', 'OPENxUSD', 'ORCLxUSD', 'PALLxUSD', 'PEPxUSD', 'PFExUSD', 'PGxUSD', 'PLTRxUSD', 'PMxUSD', 
    'PPLTxUSD', 'QQQxUSD', 'SCHFxUSD', 'SLVxUSD', 'SPYxUSD', 'STRCxUSD', 'TBLLxUSD', 'TMOxUSD', 'TONXxUSD', 'TQQQxUSD',
    'TSLAxUSD', 'UNHxUSD', 'VxUSD', 'VTIxUSD', 'VTxUSD', 'XOMxUSD','GLDxUSD', 'SLVxUSD', 'PALLxUSD', 'PPLTxUSD', 'COPXxUSD'
]

router = APIRouter()

@router.get("/check-stocks")
def check_stocks():
    
    url = "https://api.kraken.com/0/public/Ticker"    
    params = {"pair": ",".join(xstocks_list), 
              "asset_class": "tokenized_asset" }
    
    try:
        response = requests.get(url, params=params, timeout=10).json()
        
        if response.get("error"):
            return {"status": "error", "message": response["error"]}

        data = response["result"]
        results = []

        for pair_name, info in data.items():
            current_price = float(info["c"][0])
            volume = float(info["v"][0])
            trade_count = float(info["t"][0])
            
            results.append({
                "ticker": pair_name, #.replace("XUSD", "x"),
                "price": current_price,
                "volume": volume,
                "trade_count": trade_count
            })

        return results
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

