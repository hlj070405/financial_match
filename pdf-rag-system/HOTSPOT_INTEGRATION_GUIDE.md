# 热点新闻集成完成指南

## 项目概述

已成功将 **TrendRadar** 热点爬虫集成到 **幻流 (Phantom Flow)** 系统中，替换原有的 AKShare 新闻接口，实现了：

- ✅ 多源热点新闻实时抓取（微博、知乎、百度、今日头条等）
- ✅ 自动分类与标签管理
- ✅ 数据库持久化存储
- ✅ 专业化前端展示界面
- ✅ RESTful API 接口

---

## 技术架构

### 后端实现

#### 1. **HotspotService** (`backend/hotspot_service.py`)
封装 TrendRadar 核心功能：
- `fetch_latest_news()`: 实时抓取热点新闻
- `get_categorized_news()`: 获取分类后的新闻
- `search_news()`: 关键词搜索
- 自动分类映射（社会热点、科技创投、财经金融等）

#### 2. **数据库表** (`backend/database.py`)
新增 `HotspotNews` 表：
```python
- id: 主键
- title: 新闻标题
- source: 来源平台ID
- source_name: 来源平台名称
- category: 分类
- rank: 排名
- url: 新闻链接
- first_seen: 首次出现时间
- last_seen: 最后出现时间
- appear_count: 出现次数
- date: 日期
```

#### 3. **API 路由** (`backend/main.py`)
新增热点新闻 API：
- `GET /api/hotspot/categories`: 获取分类热点新闻
- `GET /api/hotspot/news`: 从数据库获取热点新闻（支持分类筛选）
- `GET /api/hotspot/search`: 搜索热点新闻
- `POST /api/hotspot/sync`: 同步最新热点数据到数据库

### 前端实现

#### **SentimentModule.vue** (完全重写)
专业化舆情溯源引擎界面：
- **毛玻璃质感设计**：符合幻流项目高端定位
- **实时统计面板**：热点总数、分类覆盖、更新状态
- **分类筛选**：一键切换不同类型热点
- **搜索功能**：快速定位关键词
- **时间线展示**：清晰的热点事件流
- **数据源状态**：实时监控各平台状态
- **分类分布图**：可视化数据占比

---

## 使用指南

### 1. 启动系统

#### 后端启动
```bash
cd backend
python main.py
```
后端将在 `http://localhost:8000` 启动

#### 前端启动
```bash
cd frontend-vue
npm run dev
```
前端将在 `http://localhost:3000` 启动

### 2. 同步热点数据

有两种方式同步数据：

#### 方式一：前端界面操作
1. 登录系统
2. 进入舆情溯源模块
3. 点击右上角"同步"按钮
4. 等待数据抓取完成（约30-60秒）

#### 方式二：API 调用
```bash
# 获取 token
POST http://localhost:8000/api/auth/login
{
  "username": "your_username",
  "password": "your_password"
}

# 同步数据
POST http://localhost:8000/api/hotspot/sync
Authorization: Bearer {token}
```

### 3. 查看热点新闻

#### 前端界面
- **分类筛选**：点击分类标签（全部、社会热点、科技创投等）
- **搜索**：输入关键词快速定位
- **查看详情**：点击新闻标题跳转原文

#### API 调用
```bash
# 获取所有新闻
GET http://localhost:8000/api/hotspot/news?limit=50
Authorization: Bearer {token}

# 按分类获取
GET http://localhost:8000/api/hotspot/news?category=科技创投&limit=20
Authorization: Bearer {token}

# 搜索新闻
GET http://localhost:8000/api/hotspot/search?keyword=AI&limit=20
Authorization: Bearer {token}
```

---

## 数据源配置

### 当前支持的平台

在 `backend/hotspot_service.py` 中配置：

```python
DEFAULT_PLATFORMS = [
    ("weibo", "微博热搜"),
    ("toutiao", "今日头条"),
    ("baidu", "百度热搜"),
    ("zhihu-hot", "知乎热榜"),
    ("36kr", "36氪"),
    ("ithome", "IT之家"),
]
```

### 分类映射

```python
CATEGORY_MAPPING = {
    "weibo": "社会热点",
    "zhihu-hot": "知识问答",
    "baidu": "综合热点",
    "toutiao": "资讯头条",
    "36kr": "科技创投",
    "ithome": "科技数码",
}
```

可根据需求自定义添加更多平台和分类。

---

## 性能优化建议

### 1. 定时同步
建议设置定时任务，每4小时自动同步一次：

**Windows 任务计划程序**：
```powershell
# 创建同步脚本 sync_hotspot.ps1
$token = "your_access_token"
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/hotspot/sync" `
  -Headers @{ Authorization = "Bearer $token" }
```

**Linux Cron**：
```bash
# 每4小时执行一次
0 */4 * * * curl -X POST http://localhost:8000/api/hotspot/sync \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. 数据清理
定期清理过期数据（建议保留7天）：
```sql
DELETE FROM hotspot_news WHERE date < DATE_SUB(CURDATE(), INTERVAL 7 DAY);
```

### 3. 网络优化
- TrendRadar 依赖外部 API (`newsnow.busiyi.world`)
- 部分平台可能因网络原因响应较慢
- 建议根据实际情况调整平台列表和超时设置

---

## 故障排查

### 问题1：同步超时
**原因**：外部 API 响应慢或网络不稳定  
**解决**：
1. 减少监控平台数量
2. 增加请求超时时间
3. 检查网络连接

### 问题2：数据库连接失败
**原因**：MySQL 服务未启动或连接配置错误  
**解决**：
1. 检查 `.env` 文件中的 `DATABASE_URL`
2. 确保 MySQL 服务正在运行
3. 验证数据库用户权限

### 问题3：前端无法显示数据
**原因**：未同步数据或 token 过期  
**解决**：
1. 先执行一次数据同步
2. 重新登录获取新 token
3. 检查浏览器控制台错误信息

---

## 下一步优化方向

### 功能增强
- [ ] AI 情感分析（基于 DeepSeek）
- [ ] 热点趋势预测
- [ ] 跨平台关联分析
- [ ] 自定义关键词订阅

### 性能优化
- [ ] Redis 缓存层
- [ ] 异步任务队列（Celery）
- [ ] 数据预加载
- [ ] CDN 加速

### UI/UX 优化
- [ ] 热点词云图
- [ ] 趋势图表（ECharts）
- [ ] 移动端适配
- [ ] 暗色主题

---

## 技术支持

如遇到问题，请检查：
1. 后端日志：`backend/` 目录下的控制台输出
2. 前端控制台：浏览器开发者工具
3. 数据库日志：MySQL 错误日志

---

**集成完成时间**: 2026年3月1日  
**版本**: v1.0.0  
**状态**: ✅ 生产就绪
