# 2026.02.12  10.00
from fastapi import APIRouter
import requests

router = APIRouter()

@router.get("/check-stocks")

xstocks = ['AAPLxUSD', 'AAPLxUSD', 'ABBVxUSD', 'ABBVxUSD', 'ABTxUSD', 'ABTxUSD', 'ACNxUSD', 'ACNxUSD', 'AMBRxUSD', 'AMBRxUSD', 
 'AMDxUSD', 'AMDxUSD', 'AMZNxUSD', 'AMZNxUSD', 'APPxUSD', 'APPxUSD', 'AVGOxUSD', 'AVGOxUSD', 'AZNxUSD', 'AZNxUSD',
 'BACxUSD', 'BACxUSD', 'BMNRxUSD', 'BMNRxUSD', 'BRK.BxUSD', 'BRK.BxUSD', 'BTBTxUSD', 'BTBTxUSD', 'BTGOxUSD', 'BTGOxUSD',
 'CMCSAxUSD', 'CMCSAxUSD', 'COINxUSD', 'COINxUSD', 'COPXxUSD', 'COPXxUSD', 'CRCLxUSD', 'CRCLxUSD', 'CRMxUSD', 'CRMxUSD',
 'CRWDxUSD', 'CRWDxUSD', 'CSCOxUSD', 'CSCOxUSD', 'CVXxUSD', 'CVXxUSD', 'DFDVxUSD', 'DFDVxUSD', 'DHRxUSD', 'DHRxUSD', 
 'GLDxUSD', 'GLDxUSD', 'GMExUSD', 'GMExUSD', 'GOOGLxUSD', 'GOOGLxUSD', 'GSxUSD', 'GSxUSD', 'HONxUSD', 'HONxUSD', 
 'HOODxUSD', 'HOODxUSD', 'IBMxUSD', 'IBMxUSD', 'IEMGxUSD', 'IEMGxUSD', 'IJRxUSD', 'IJRxUSD', 'INTCxUSD', 'INTCxUSD', 
 'IWMxUSD', 'IWMxUSD', 'JNJxUSD', 'JNJxUSD', 'JPMxUSD', 'JPMxUSD', 'KOxUSD', 'KOxUSD', 'KRAQxUSD', 'KRAQxUSD', 
 'LINxUSD', 'LINxUSD', 'LLYxUSD', 'LLYxUSD', 'MCDxUSD', 'MCDxUSD', 'MDTxUSD', 'MDTxUSD', 'METAxUSD', 'METAxUSD',
 'MRKxUSD', 'MRKxUSD', 'MRVLxUSD', 'MRVLxUSD', 'MSFTxUSD', 'MSFTxUSD', 'MSTRxUSD', 'MSTRxUSD', 'NFLXxUSD', 'NFLXxUSD', 
 'NVDAxUSD', 'NVDAxUSD', 'NVOxUSD', 'NVOxUSD', 'OPENxUSD', 'OPENxUSD', 'ORCLxUSD', 'ORCLxUSD', 'PALLxUSD', 'PALLxUSD', 
 'PEPxUSD', 'PEPxUSD', 'PFExUSD', 'PFExUSD', 'PGxUSD', 'PGxUSD', 'PLTRxUSD', 'PLTRxUSD', 'PMxUSD', 'PMxUSD', 
 'PPLTxUSD', 'PPLTxUSD', 'QQQxUSD', 'QQQxUSD', 'SCHFxUSD', 'SCHFxUSD', 'SLVxUSD', 'SLVxUSD', 'SPYxUSD', 'SPYxUSD', 
 'STRCxUSD', 'STRCxUSD', 'TBLLxUSD', 'TBLLxUSD', 'TMOxUSD', 'TMOxUSD', 'TONXxUSD', 'TONXxUSD', 'TQQQxUSD', 'TQQQxUSD',
 'TSLAxUSD', 'TSLAxUSD', 'UNHxUSD', 'UNHxUSD', 'VxUSD', 'VTIxUSD', 'VTIxUSD', 'VTxUSD', 'VTxUSD', 'VxUSD', 'XOMxUSD', 'XOMxUSD']

def check_stocks():
    url = "https://api.kraken.com/0/public/Ticker"    
    params = {"pair": xstocks, "asset_class": "tokenized_asset" }
    
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
