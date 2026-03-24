# 幻流系统 - 用户认证模块

## 功能说明

已实现完整的用户认证系统，包括：
- 用户注册
- 用户登录
- JWT Token 认证
- 密码加密存储（bcrypt）
- MySQL 数据库存储

## 数据库配置

### 1. 创建 MySQL 数据库

```sql
CREATE DATABASE phantom_flow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 配置环境变量

在 `backend/.env` 文件中配置：

```env
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/phantom_flow
SECRET_KEY=your-secret-key-change-this-in-production
```

### 3. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
python init_db.py
```

这将创建所需的表并生成一个默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`
- 邮箱: `admin@phantomflow.com`

## API 端点

### 用户注册
```
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "full_name": "测试用户"
}
```

### 用户登录
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@phantomflow.com",
    "full_name": "系统管理员",
    "created_at": "2026-02-13T13:00:00"
  }
}
```

### 获取当前用户信息
```
GET /api/auth/me
Authorization: Bearer <access_token>
```

## 前端集成

前端已更新 `App.vue`，登录功能会：
1. 调用后端 `/api/auth/login` API
2. 将返回的 token 存储到 localStorage
3. 显示登录成功/失败消息

## 数据库表结构

### users 表
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);
```

## 安全特性

- ✓ 密码使用 bcrypt 加密存储
- ✓ JWT Token 有效期 7 天
- ✓ Token 包含用户身份信息
- ✓ 支持 Token 刷新机制
- ✓ 防止 SQL 注入（使用 SQLAlchemy ORM）
- ✓ CORS 配置支持跨域请求

## 启动服务

```bash
cd backend
python main.py
```

服务将在 `http://localhost:8000` 启动。

## 测试

使用默认管理员账户测试登录：
- 用户名: `admin`
- 密码: `admin123`
