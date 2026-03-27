import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../pdf-rag-system/backend')))

import chromadb
from chromadb.config import Settings

CHROMA_PERSIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../pdf-rag-system/backend/chroma_db'))

def check():
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    
    collections = client.list_collections()
    
    for c in collections:
        print(f"Collection: {c.name}")
        # Get all metadatas to see what files are actually in there
        try:
            data = c.get(include=["metadatas"])
            sources = set()
            for meta in data['metadatas']:
                if meta and 'source' in meta:
                    sources.add(meta['source'])
            print("Files in vector DB:")
            for s in sources:
                print(f" - {s}")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    check()
