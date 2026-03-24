
import os

env_content = """DIFY_API_URL=http://127.0.0.1/v1
DIFY_API_KEY=app-SaBpXTB7EOlHi1lvqUxtgAbq

# Database Configuration
DATABASE_URL=mysql+pymysql://root:1234@127.0.0.1:3306/phantom_flow

# JWT Configuration
SECRET_KEY=phantom-flow-secret-key-2026
DEEPSEEK_API_KEY=sk-jncmmbnconojuxhpoilrpngpyrjisczosqzmvgbcxlilftkj
"""

file_path = os.path.join(os.getcwd(), 'backend', '.env')
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(env_content)

print(f"Successfully wrote to {file_path}")
