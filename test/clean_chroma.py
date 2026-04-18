import os
import shutil

chroma_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../pdf-rag-system/backend/chroma_db'))

if os.path.exists(chroma_dir):
    for item in os.listdir(chroma_dir):
        item_path = os.path.join(chroma_dir, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
            print(f"Deleted: {item_path}")
        except Exception as e:
            print(f"Failed to delete {item_path}. Reason: {e}")
    print("ChromaDB cleared successfully.")
else:
    print("ChromaDB directory not found.")
