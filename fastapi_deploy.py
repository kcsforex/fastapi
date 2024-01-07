
# 2024.01.07  19.00
import pandas as pd 
import sqlite3
import json as js

sqlite_conn = sqlite3.connect('formula1.db',check_same_thread=False)

from fastapi import FastAPI
query_server = FastAPI()

@query_server.get('/')
def default_route():
    return {"message":"serving data from races table"}

@query_server.get('/query_data')
def query_data():
    query1_data  = pd.read_sql("""SELECT * FROM races LIMIT 10""",sqlite_conn)
    query1_json = query1_data.to_json(orient ='records')
    print(js.loads(query1_json))
    return js.loads(query1_json)

#import nest_asyncio
#import uvicorn
#if __name__ == "__main__":
#    nest_asyncio.apply()
#    uvicorn.run(query_server)


