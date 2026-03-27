import os
import sys

# add backend to path
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
    print(f"Found {len(collections)} collections")
    
    for c in collections:
        print(f"\n--- Collection: {c.name} ---")
        try:
            print(f"Count: {c.count()}")
            # peek 
            peek_data = c.peek(limit=1)
            if peek_data and peek_data.get('metadatas') and len(peek_data['metadatas']) > 0:
                print("Sample metadata:", peek_data['metadatas'][0])
            
            # Query
            results = c.query(
                query_texts=["宁德时代", "比亚迪", "贵州茅台"],
                n_results=2
            )
            print(f"Query results for '宁德时代, 比亚迪, 贵州茅台':")
            if results and results.get('documents'):
                for i, docs in enumerate(results['documents']):
                    query = ["宁德时代", "比亚迪", "贵州茅台"][i]
                    print(f"  Query: {query}")
                    for j, doc in enumerate(docs):
                        meta = results['metadatas'][i][j]
                        print(f"    - Doc snippet: {doc[:100]}... | Meta: {meta}")
            
        except Exception as e:
            print("Error querying collection:", e)

if __name__ == "__main__":
    check()
