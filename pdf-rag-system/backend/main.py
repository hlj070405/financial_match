import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import FINANCIAL_REPORTS_DIR
from database import init_db
from routers import auth, chat, file, economic, hotspot, tushare, diagnosis, watchlist, agent, rag, chain

app = FastAPI(title="PDF RAG Analysis System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _startup_event():
    init_db()

# 挂载静态文件目录，使财报PDF可通过HTTP访问
if not os.path.exists(FINANCIAL_REPORTS_DIR):
    os.makedirs(FINANCIAL_REPORTS_DIR)
app.mount("/financial_reports", StaticFiles(directory=FINANCIAL_REPORTS_DIR), name="financial_reports")

# 注册路由
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(file.router)
app.include_router(economic.router)
app.include_router(hotspot.router)
app.include_router(tushare.router)
app.include_router(diagnosis.router)
app.include_router(watchlist.router)
app.include_router(agent.router)
app.include_router(rag.router)
app.include_router(chain.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


print(f"[启动] RAG引擎: LangChain + ChromaDB (本地向量库)")
print(f"[启动] Embedding: BAAI/bge-large-zh-v1.5 via SiliconFlow")
print(f"[启动] 财报PDF目录已挂载: {FINANCIAL_REPORTS_DIR}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

