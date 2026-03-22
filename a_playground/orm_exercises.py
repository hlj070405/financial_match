"""
SQLAlchemy ORM 循序渐进练习
请按照提示填写空白处，运行测试你的答案
"""

# ===== 准备工作 =====
# 先运行这部分代码建立测试环境
import string
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# 创建内存数据库用于练习
engine = create_engine("sqlite:///:memory:", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ===== 练习1：定义一个简单的User模型 =====
# 任务：补全User类的定义
class User(Base):
    __tablename__ = "users"
    
    # 已经给你写好的字段
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    
    # TODO: 添加以下字段：
    # 1. email - 字符串类型，最大长度100，可以为空
    email =Column(String(100), nullable=True)
    # 2. age - 整数类型，可以为空
    age = Column(Integer, nullable=True)
    # 3. created_at - 日期时间类型，默认值为当前时间
    created_at = Column(DateTime, default=datetime.utcnow)
    

# ===== 练习2：定义带关系的Post模型 =====
# 任务：创建Post模型，并与User建立关系
class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # TODO: 添加外键关联到users表的id字段
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # TODO: 添加relationship关系
    user = relationship("User", back_populates="posts")
    
    # 在这里填写你的答案：
    pass


# 为User添加反向关系（补全这个）
# User.posts = relationship(___, back_populates=___)
# 问题1:back_populates什么意思详细解释:
# back_populates是SQLAlchemy中用于定义双向关系的参数。
# 当你在两个模型之间建立关系时，使用back_populates可以确保两个方向的关系都能正常工作。
# 例如：User.posts = relationship("Post", back_populates="user")
#      Post.user = relationship("User", back_populates="posts")
# 这样，当你访问user.posts时，会得到该用户的所有帖子；
# 当你访问post.user时，会得到该帖子的作者。
#问题2: 为什么需要双向关系？
#答: 双向关系可以让你从两个角度访问数据，提高查询的灵活性和效率。
#问题3: 如果不使用back_populates，会有什么问题？
#答: 不使用back_populates，你只能从一个方向访问数据，无法从另一个方向访问。
#问题4:建立联系后怎么从另一个方向访问?
#答: 建立联系后，你可以通过另一个方向访问数据，例如：user.posts可以访问该用户的所有帖子，post.user可以访问该帖子的作者。
#问题5:这是不是在多对多场景下非常好用?
#答: 是的，在多对多场景下非常好用。
#问题6:除了这样使用relationship还能怎么用?
#答: 除了这样使用relationship，还可以使用其他参数来控制关系的行为，例如：cascade、lazy、uselist等。
#详细讲讲:
#cascade: 控制级联操作，例如：cascade="all, delete-orphan"
#lazy: 控制关系的加载方式，例如：lazy="select"、lazy="joined"、lazy="subquery"、lazy="selectin"、lazy="dynamic"
#uselist: 控制关系是否为列表，例如：uselist=True、uselist=False
#级联操作是不是通常是父子关系:
#答: 是的，级联操作通常是父子关系。例如：cascade="all, delete-orphan"表示当父对象被删除时，子对象也会被删除。
#orphan是什么意思:
#答: orphan是指孤立的对象，即没有父对象的对象。例如：cascade="all, delete-orphan"表示当父对象被删除时，子对象也会被删除。
#lazy是什么意思:
#答: lazy是指关系的加载方式。例如：lazy="select"表示关系在访问时才加载，lazy="joined"表示关系在查询时一起加载。
#uselist什么意思:
#答: uselist是指关系是否为列表。例如：uselist=True表示关系为列表，uselist=False表示关系为单个对象。



# ===== 练习3：创建数据库表 =====
def create_tables():
    """创建所有表"""
    # TODO: 调用Base的方法创建所有表
    # Base.___.___(bind=___)
    pass


# ===== 练习4：创建和查询数据 =====
def practice_crud():
    """CRUD操作练习"""
    session = Session()
    
    # TODO 4.1: 创建一个新用户
    # 创建一个用户名为"张三"，email为"zhangsan@example.com"，年龄为25的用户
    # new_user = User(username=___, email=___, age=___)
    # session.___(new_user)
    # session.___()
    
    # TODO 4.2: 查询用户
    # 查询用户名为"张三"的用户
    # user = session.___(User).___(User.username == ___).___()
    # print(f"查询到的用户: {user.username}, {user.email}")
    
    # TODO 4.3: 更新用户
    # 将张三的年龄更新为26
    # user.___ = 26
    # session.___()
    
    # TODO 4.4: 创建文章
    # 为张三创建一篇文章
    # new_post = Post(title=___, content=___, user_id=___)
    # session.___(new_post)
    # session.___()
    
    # TODO 4.5: 关联查询
    # 查询张三的所有文章
    # user = session.___(User).___(User.username == "张三").___()
    # posts = user.___  # 通过relationship访问
    # print(f"张三的文章数量: {len(posts)}")
    
    session.close()


# ===== 练习5：复杂查询 =====
def practice_queries():
    """复杂查询练习"""
    session = Session()
    
    # TODO 5.1: 查询所有用户并按年龄排序
    # users = session.___(User).___(User.age).___()
    # for user in users:
    #     print(f"{user.username}: {user.age}岁")
    
    # TODO 5.2: 条件查询 - 查询年龄大于20的用户
    # users = session.___(User).___(User.age ___ 20).___()
    # print(f"年龄大于20的用户有: {len(users)}个")
    
    # TODO 5.3: 限制查询数量 - 只查询前2个用户
    # users = session.___(User).___(2).___()
    
    # TODO 5.4: 统计查询 - 统计用户总数
    # count = session.___(User).___()
    # print(f"用户总数: {count}")
    
    session.close()


# ===== 练习6：使用聚合函数 =====
def practice_aggregation():
    """聚合查询练习"""
    session = Session()
    
    # 需要先导入func
    from sqlalchemy import func
    
    # TODO 6.1: 计算所有用户的平均年龄
    # result = session.___(func.___(User.age)).___()
    # avg_age = result[0][0]
    # print(f"平均年龄: {avg_age}")
    
    # TODO 6.2: 按年龄分组统计用户数量
    # result = session.___(
    #     User.age, 
    #     func.___(User.id)
    # ).___(User.age).___()
    # for age, count in result:
    #     print(f"{age}岁: {count}人")
    
    session.close()


# ===== 运行测试函数 =====
if __name__ == "__main__":
    print("=== ORM练习开始 ===")
    
    # 1. 创建表
    print("\n1. 创建数据库表...")
    create_tables()
    print("✓ 表创建成功")
    
    # 2. CRUD练习
    print("\n2. CRUD操作练习...")
    practice_crud()
    print("✓ CRUD操作完成")
    
    # 3. 查询练习
    print("\n3. 查询练习...")
    practice_queries()
    print("✓ 查询练习完成")
    
    # 4. 聚合练习
    print("\n4. 聚合查询练习...")
    practice_aggregation()
    print("✓ 聚合查询完成")
    
    print("\n=== 所有练习完成！ ===")


# ===== 答案提示 =====
"""
需要帮助时查看这里：

练习1:
- email = Column(String(100), nullable=True)
- age = Column(Integer, nullable=True)
- created_at = Column(DateTime, default=datetime.utcnow)

练习2:
- user_id = Column(Integer, ForeignKey('users.id'))
- user = relationship('User', back_populates='posts')
- User.posts = relationship('Post', back_populates='user')

练习3:
- Base.metadata.create_all(bind=engine)

练习4:
- new_user = User(username="张三", email="zhangsan@example.com", age=25)
- session.add(new_user)
- session.commit()
- user = session.query(User).filter(User.username == "张三").first()
- user.age = 26
- session.commit()
- new_post = Post(title="我的第一篇文章", content="这是文章内容", user_id=user.id)
- session.add(new_post)
- session.commit()
- user = session.query(User).filter(User.username == "张三").first()
- posts = user.posts

练习5:
- users = session.query(User).order_by(User.age).all()
- users = session.query(User).filter(User.age > 20).all()
- users = session.query(User).limit(2).all()
- count = session.query(User).count()

练习6:
- result = session.query(func.avg(User.age)).first()
- result = session.query(User.age, func.count(User.id)).group_by(User.age).all()
"""
