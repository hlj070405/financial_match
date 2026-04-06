from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, text
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 数据库连接配置
# 从环境变量获取，或者使用默认值
# 注意：务必确保使用 utf8mb4 字符集
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:1234@127.0.0.1:3306/phantom_flow"
)

# 确保 URL 中包含 charset=utf8mb4，如果已经在 connect_args 中指定则也可以
if "charset=utf8mb4" not in SQLALCHEMY_DATABASE_URL:
    if "?" in SQLALCHEMY_DATABASE_URL:
        SQLALCHEMY_DATABASE_URL += "&charset=utf8mb4"
    else:
        SQLALCHEMY_DATABASE_URL += "?charset=utf8mb4"

# 创建数据库引擎
# connect_args={"charset": "utf8mb4"} 确保连接层面也使用正确的字符集
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"charset": "utf8mb4"},
    pool_pre_ping=True,
    pool_recycle=3600
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 定义股票模型
class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, comment="股票代码")
    name = Column(String(50), index=True, comment="股票名称")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

# 定义文档模型（PDF工作区）
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    source = Column(String(50), default="cninfo", comment="来源: cninfo/upload/manual")
    title = Column(String(200), nullable=True, comment="展示标题")
    company = Column(String(100), nullable=True, index=True, comment="公司")
    stock_code = Column(String(20), nullable=True, index=True, comment="股票代码")
    year = Column(Integer, nullable=True, index=True, comment="年份")
    pdf_path = Column(String(500), nullable=False, comment="PDF相对路径")
    sha256 = Column(String(64), nullable=True, index=True, comment="文件hash(可选)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        UniqueConstraint('user_id', 'pdf_path', name='uq_documents_user_pdf_path'),
    )

# 定义用户模型
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, comment="用户名")
    hashed_password = Column(String(100), comment="加密密码")
    full_name = Column(String(100), nullable=True, comment="全名")
    email = Column(String(100), nullable=True, index=True, comment="邮箱")
    disabled = Column(Integer, default=0, comment="是否禁用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

# 定义聊天历史模型
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, comment="用户ID")
    conversation_id = Column(String(50), unique=True, index=True, comment="会话ID")
    title = Column(String(200), comment="会话标题")
    first_message = Column(Text, comment="首条消息")
    messages = Column(Text, comment="消息历史JSON")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

# 定义自选股模型
class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    ts_code = Column(String(20), nullable=False, comment="股票代码(如000001.SZ)")
    name = Column(String(50), nullable=False, comment="股票名称")
    sort_order = Column(Integer, default=0, comment="排序序号")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        UniqueConstraint('user_id', 'ts_code', name='uq_watchlist_user_ts_code'),
    )

# 定义热点新闻模型
class HotspotNews(Base):
    __tablename__ = "hotspot_news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True, comment="新闻标题")
    source = Column(String(50), index=True, comment="来源平台ID")
    source_name = Column(String(100), comment="来源平台名称")
    category = Column(String(50), index=True, comment="分类")
    rank = Column(Integer, comment="排名")
    url = Column(String(500), comment="新闻链接")
    mobile_url = Column(String(500), comment="移动端链接")
    first_seen = Column(DateTime, comment="首次出现时间")
    last_seen = Column(DateTime, comment="最后出现时间")
    appear_count = Column(Integer, default=1, comment="出现次数")
    date = Column(String(20), index=True, comment="日期(YYYY-MM-DD)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

# 虚拟持仓 - 投资组合
class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    name = Column(String(100), default="默认组合", comment="组合名称")
    initial_cash = Column(Integer, default=100000, comment="初始资金(分)")
    commission_rate = Column(Integer, default=25, comment="佣金费率(万分之)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

# 虚拟持仓 - 交易流水
class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, index=True, nullable=False, comment="组合ID")
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    ts_code = Column(String(20), nullable=False, comment="股票代码(如000001.SZ)")
    stock_name = Column(String(50), nullable=False, comment="股票名称")
    direction = Column(String(10), nullable=False, comment="buy/sell")
    price = Column(Integer, nullable=False, comment="成交价(分)")
    quantity = Column(Integer, nullable=False, comment="数量(股)")
    commission = Column(Integer, default=0, comment="佣金(分)")
    stamp_tax = Column(Integer, default=0, comment="印花税(分)")
    trade_date = Column(String(20), nullable=False, comment="成交日期 YYYY-MM-DD")
    notes = Column(String(500), nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
