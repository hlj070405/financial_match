import os
from dotenv import load_dotenv

load_dotenv()

# Dify
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-jncmmbnconojuxhpoilrpngpyrjisczosqzmvgbcxlilftkj")

# Auth
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# 测试账号（已在数据库中注册）
TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin123")
TEST_BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:8000")

# Tushare
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "ObsmUviSthlgoqudvpkzWwUiPDcChmEHlxymCfCPbJXQDHReIprUGmGjGOdhXNNK")
TUSHARE_HTTP_PROXY = os.getenv("TUSHARE_HTTP_PROXY", "")
TUSHARE_HTTP_URL = os.getenv("TUSHARE_HTTP_URL", "http://121.40.135.59:8010/")

# Kimi (Moonshot) - LLM 主模型
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "sk-4kChNkFRINxrsfyHDvUEJwvtIR9IntwowQnxT51bfDs1Ezd2")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k2.5")
KIMI_TEMPERATURE = float(os.getenv("KIMI_TEMPERATURE", "0.6"))
KIMI_MAX_TOKENS = int(os.getenv("KIMI_MAX_TOKENS", "4096"))
KIMI_MAX_ROUNDS = int(os.getenv("KIMI_MAX_ROUNDS", "15"))

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

# RAG 分块
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5120"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "256"))

# SiliconFlow 辅助模型（标题生成等）
SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
SILICONFLOW_MODEL = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-72B-Instruct")
SILICONFLOW_TEMPERATURE = float(os.getenv("SILICONFLOW_TEMPERATURE", "0.7"))

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# ChromaDB
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))

# Paths
FINANCIAL_REPORTS_DIR = "./financial_reports"
