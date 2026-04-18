import os
import sys

# add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../pdf-rag-system/backend')))

import chromadb
from chromadb.config import Settings

def check():
    client = chromadb.HttpClient(
        host="127.0.0.1",
        port=8001,
        settings=Settings(anonymized_telemetry=False)
    )
    
    print("Heartbeat:", client.heartbeat())
    
    collections = client.list_collections()
    print(f"Found {len(collections)} collections")
    
if __name__ == "__main__":
    check()
