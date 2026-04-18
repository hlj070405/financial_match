# 幻流 (Phantom Flow) - 主界面系统说明

## 项目概述

幻流是一个多源数据驱动的金融决策进化智能体系统,提供专业的财务分析、舆情监测和智能咨询服务。

## 技术栈

### 前端
- **框架**: Vue 3 + Vite
- **路由**: Vue Router 4
- **样式**: TailwindCSS + 毛玻璃效果
- **图表**: ECharts 5
- **流程图**: Vue Flow (React Flow for Vue)
- **3D背景**: Vanta.js + Three.js
- **HTTP客户端**: Axios

### 后端
- **框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy
- **认证**: JWT (python-jose) + bcrypt
- **AI引擎**: Dify API集成

## 系统架构

```
幻流系统
├── 登录页面 (Login.vue)
│   └── Vanta Globe 3D背景
│
└── 主界面 (Dashboard.vue)
    ├── 侧边栏导航 (Sidebar.vue)
    ├── 顶部栏 (TopBar.vue)
    └── 功能模块
        ├── 幻思·智能咨询 (ChatModule.vue)
        ├── 幻化·逻辑流 (LogicFlowModule.vue)
        ├── 幻诊·运营评估 (DataVisualization.vue)
        └── 幻感·舆情溯源 (SentimentModule.vue)
```

## 核心功能模块

### 1. 幻思·智能企业咨询
- **功能**: AI驱动的财务分析对话
- **特性**: 
  - 自然语言问答
  - 思维链推理展示
  - 数据源溯源
  - 历史会话管理
- **API**: `POST /api/chat`

### 2. 幻化·逻辑流可视化
- **功能**: AI决策推理链路可视化
- **特性**:
  - 节点流程图展示
  - 推理步骤追踪
  - 数据源调用可视化
  - 支持导出推理图
- **技术**: Vue Flow

### 3. 幻诊·全景运营评估
- **功能**: 财务数据多维度分析
- **特性**:
  - 核心指标卡片
  - 营收利润趋势图
  - 业务结构饼图
  - 财务指标对比
  - 风险评估雷达图
- **技术**: ECharts

### 4. 幻感·舆情溯源引擎
- **功能**: 实时舆情监测与分析
- **特性**:
  - 舆情热度追踪
  - 热点事件时间线
  - 情感分析
  - 热词云
  - 风险预警

## 启动指南

### 前端启动

```bash
cd pdf-rag-system/frontend-vue
npm install
npm run dev
```

访问: `http://localhost:3001`

### 后端启动

```bash
cd pdf-rag-system/backend
pip install -r requirements.txt
python main.py
```

API地址: `http://localhost:8000`

### 环境配置

后端 `.env` 文件配置:
```env
DIFY_API_URL=http://localhost/v1
DIFY_API_KEY=your-dify-api-key
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/phantom_flow
SECRET_KEY=your-secret-key
```

## API接口

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 业务接口
- `POST /api/chat` - 智能对话 (需要认证)
- `POST /api/upload-pdf` - 上传PDF文件
- `POST /api/analyze` - 分析文档 (流式响应)

## 设计特点

### UI设计
- **毛玻璃质感**: `backdrop-blur-md` + 半透明背景
- **流光效果**: 渐变色 + 动画
- **专业配色**: 蓝-紫-粉渐变主题
- **无emoji**: 保持专业性
- **响应式布局**: 适配不同屏幕尺寸

### 用户体验
- **单页应用**: 无刷新切换模块
- **实时反馈**: Loading状态 + 错误提示
- **数据可视化**: 直观的图表展示
- **智能交互**: 自然语言对话

## 目录结构

```
frontend-vue/
├── src/
│   ├── components/
│   │   ├── ChatModule.vue          # 智能对话模块
│   │   ├── LogicFlowModule.vue     # 逻辑流可视化
│   │   ├── DataVisualization.vue   # 数据可视化
│   │   ├── SentimentModule.vue     # 舆情监测
│   │   ├── Sidebar.vue             # 侧边栏
│   │   ├── TopBar.vue              # 顶部栏
│   │   ├── VantaBackground.vue     # 3D背景
│   │   └── GlassButton.vue         # 毛玻璃按钮
│   ├── views/
│   │   ├── Login.vue               # 登录页
│   │   └── Dashboard.vue           # 主界面
│   ├── router/
│   │   └── index.js                # 路由配置
│   ├── App.vue                     # 根组件
│   ├── main.js                     # 入口文件
│   └── style.css                   # 全局样式
└── package.json

backend/
├── main.py                         # FastAPI主程序
├── database.py                     # 数据库模型
├── auth.py                         # 认证逻辑
├── schemas.py                      # Pydantic模型
└── .env                            # 环境变量
```

## 下一步开发建议

### 短期优化
1. **完善Dify集成**: 配置实际的Dify工作流
2. **数据库初始化**: 创建测试用户
3. **错误处理**: 完善前端错误提示
4. **加载状态**: 优化各模块的加载动画

### 中期功能
1. **Mem0集成**: 实现用户记忆系统
2. **报告生成**: PDF/Markdown报告导出
3. **实时数据**: WebSocket实时舆情推送
4. **多语言支持**: i18n国际化

### 长期规划
1. **移动端适配**: 响应式优化
2. **权限系统**: 角色权限管理
3. **数据看板**: 自定义仪表盘
4. **API文档**: Swagger/OpenAPI集成

## 常见问题

### Q: 登录失败怎么办?
A: 确保后端服务已启动,检查 `.env` 配置,首次使用需要先注册用户。

### Q: 图表不显示?
A: 检查ECharts是否正确加载,确保容器有明确的高度。

### Q: Vue Flow样式异常?
A: 确保导入了所有必要的CSS文件:
```js
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
```

### Q: 如何对接真实的Dify服务?
A: 修改后端 `.env` 中的 `DIFY_API_URL` 和 `DIFY_API_KEY`,确保Dify工作流已配置。

## 联系方式

- 项目名称: 幻流 (Phantom Flow)
- 版本: 1.0.0
- 更新时间: 2026-02-22

---

**注意**: 这是开发版本,生产环境部署前请修改所有默认密钥和配置。
