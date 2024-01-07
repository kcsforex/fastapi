
# 2024.01.07  11.00
import pandas as pd 
import sqlite3
import json as js

sqlite_conn = sqlite3.connect('api_data.db',check_same_thread=False)

from fastapi import FastAPI
query_server = FastAPI()

@query_server.get('/')
def default_route():
    return {"message":"serving data from hacker_data table"}

@query_server.get('/query_data')
def query_data():
    """The function returns the 10 records 
    in the hacker_data table"""
    query1 = """SELECT * FROM hacker_data LIMIT 10"""
    query1_data  = pd.read_sql("""SELECT * FROM hacker_data LIMIT 10""",sqlite_conn)
    query1_json = query1_data.to_json(orient ='records')
    #we are loading the json object from string object below
    print(js.loads(query1_json))
    return js.loads(query1_json)

import nest_asyncio
import uvicorn
if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(query_server)


