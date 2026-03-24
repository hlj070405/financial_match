import os
from dotenv import load_dotenv

load_dotenv()

# Dify
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Auth
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Paths
FINANCIAL_REPORTS_DIR = "./financial_reports"
