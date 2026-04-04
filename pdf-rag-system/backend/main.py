import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import FINANCIAL_REPORTS_DIR
from core.database import init_db
from auth.api import router as auth_router
from chat.api import router as chat_router
from report.api import router as report_router
from economic.api import router as economic_router
from hotspot.api import router as hotspot_router
from market.api import router as market_router
from market.watchlist_api import router as watchlist_router
from diagnosis.api import router as diagnosis_router
from agent.api import router as agent_router
from rag.api import router as rag_router
from agent.chain_api import router as chain_router

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
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(report_router)
app.include_router(economic_router)
app.include_router(hotspot_router)
app.include_router(market_router)
app.include_router(watchlist_router)
app.include_router(diagnosis_router)
app.include_router(agent_router)
app.include_router(rag_router)
app.include_router(chain_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


print(f"[启动] RAG引擎: LangChain + ChromaDB (本地向量库)")
print(f"[启动] Embedding: BAAI/bge-large-zh-v1.5 via SiliconFlow")
print(f"[启动] 财报PDF目录已挂载: {FINANCIAL_REPORTS_DIR}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

