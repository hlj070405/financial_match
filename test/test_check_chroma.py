import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../pdf-rag-system/backend')))

from services.rag_service import rag_service

async def check_db():
    try:
        # Check overall stats
        stats = await rag_service.get_stats("test_user") # Assuming user_id='test_user' or we can check all collections
        print("Stats for 'test_user':", stats)
        
        # Or just directly access chromadb
        collections = rag_service.chroma_client.list_collections()
        print("Collections:", [c.name for c in collections])
        
        for c in collections:
            print(f"Collection: {c.name}, count: {c.count()}")
            # try to query
            results = c.query(
                query_texts=["比亚迪", "宁德时代"],
                n_results=5
            )
            print(f"Results for '{c.name}':", results)
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_db())
