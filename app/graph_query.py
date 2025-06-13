# graph_query.py
import requests
import json

GRAPHQL_URL = "https://api.studio.thegraph.com/query/111711/capstone/version/latest"

def fetch_trade_closes():
    query = """
    {
      tradeCloses(first: 1000, orderBy: blockTimestamp, orderDirection: desc) {
        tradeNum
        blockTimestamp
      }
    }
    """
    try:
        res = requests.post(
            GRAPHQL_URL,
            json={'query': query},
            headers={"Content-Type": "application/json"}
        )
        data = res.json()["data"]["tradeCloses"]
        return [
            {
                "trade_num": int(d["tradeNum"]),
                "auction_date": int(d["blockTimestamp"])
            } for d in data
        ]
    except Exception as e:
        print("GraphQL 오류:", e)
        return []
