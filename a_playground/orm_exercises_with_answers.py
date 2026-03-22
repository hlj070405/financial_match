"""
SQLAlchemy ORM 循序渐进练习 - 带答案版本
请先尝试自己完成，再对照答案
"""

# ===== 准备工作 =====
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

engine = create_engine("sqlite:///:memory:", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ===== 练习1：定义一个简单的User模型 =====
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    
    # 答案：
    email = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    

# ===== 练习2：定义带关系的Post模型 =====
class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 答案：
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='posts')

# 答案：
User.posts = relationship('Post', back_populates='user')


# ===== 练习3：创建数据库表 =====
def create_tables():
    """创建所有表"""
    # 答案：
    Base.metadata.create_all(bind=engine)


# ===== 练习4：创建和查询数据 =====
def practice_crud():
    """CRUD操作练习"""
    session = Session()
    
    # 答案 4.1:
    new_user = User(username="张三", email="zhangsan@example.com", age=25)
    session.add(new_user)
    session.commit()
    
    # 答案 4.2:
    user = session.query(User).filter(User.username == "张三").first()
    print(f"查询到的用户: {user.username}, {user.email}")
    
    # 答案 4.3:
    user.age = 26
    session.commit()
    
    # 答案 4.4:
    new_post = Post(title="我的第一篇文章", content="这是文章内容", user_id=user.id)
    session.add(new_post)
    session.commit()
    
    # 答案 4.5:
    user = session.query(User).filter(User.username == "张三").first()
    posts = user.posts
    print(f"张三的文章数量: {len(posts)}")
    
    session.close()


# ===== 练习5：复杂查询 =====
def practice_queries():
    """复杂查询练习"""
    session = Session()
    
    # 答案 5.1:
    users = session.query(User).order_by(User.age).all()
    for user in users:
        print(f"{user.username}: {user.age}岁")
    
    # 答案 5.2:
    users = session.query(User).filter(User.age > 20).all()
    print(f"年龄大于20的用户有: {len(users)}个")
    
    # 答案 5.3:
    users = session.query(User).limit(2).all()
    
    # 答案 5.4:
    count = session.query(User).count()
    print(f"用户总数: {count}")
    
    session.close()


# ===== 练习6：使用聚合函数 =====
def practice_aggregation():
    """聚合查询练习"""
    session = Session()
    
    from sqlalchemy import func
    
    # 答案 6.1:
    result = session.query(func.avg(User.age)).first()
    avg_age = result[0]
    print(f"平均年龄: {avg_age}")
    
    # 答案 6.2:
    result = session.query(
        User.age, 
        func.count(User.id)
    ).group_by(User.age).all()
    for age, count in result:
        print(f"{age}岁: {count}人")
    
    session.close()


# ===== 运行测试函数 =====
if __name__ == "__main__":
    print("=== ORM练习（带答案版本）===")
    
    print("\n1. 创建数据库表...")
    create_tables()
    print("✓ 表创建成功")
    
    print("\n2. CRUD操作练习...")
    practice_crud()
    print("✓ CRUD操作完成")
    
    print("\n3. 查询练习...")
    practice_queries()
    print("✓ 查询练习完成")
    
    print("\n4. 聚合查询练习...")
    practice_aggregation()
    print("✓ 聚合查询完成")
    
    print("\n=== 所有练习完成！ ===")
