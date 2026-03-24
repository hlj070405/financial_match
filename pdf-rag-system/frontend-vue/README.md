# PDF RAG 智能分析系统 - Vue 3 前端

基于 Vue 3 + Vite 的企业财报智能分析前端应用

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **TailwindCSS** - 实用优先的 CSS 框架
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化库

## 项目结构

```
frontend-vue/
├── src/
│   ├── components/          # Vue 组件
│   │   ├── UploadArea.vue   # 文件上传组件
│   │   ├── ResultDisplay.vue # 结果展示组件
│   │   └── ChartDisplay.vue  # 图表组件
│   ├── api/                 # API 接口
│   │   └── analysis.js      # 分析相关 API
│   ├── App.vue              # 根组件
│   ├── main.js              # 入口文件
│   └── style.css            # 全局样式
├── index.html               # HTML 模板
├── vite.config.js           # Vite 配置
├── tailwind.config.js       # TailwindCSS 配置
└── package.json             # 项目依赖

## 快速开始

### 1. 安装依赖

```bash
cd frontend-vue
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录

## 功能特性

### ✅ 已实现

- 📤 **文件上传** - 支持拖拽和点击上传 PDF
- 📝 **智能分析** - 调用 Dify 工作流进行财报分析
- 📊 **数据可视化** - ECharts 图表展示
- 🎨 **现代 UI** - TailwindCSS 响应式设计
- ⚡ **快速开发** - Vite 热更新
- 🔄 **加载状态** - 优雅的加载和进度提示

### 🎯 核心组件

#### UploadArea.vue
- 文件拖拽上传
- 上传进度显示
- 分析参数配置（问题、风格）

#### ResultDisplay.vue
- 分析结果展示
- 加载状态管理
- 引用来源显示

#### ChartDisplay.vue
- ECharts 图表渲染
- 响应式图表
- 多种图表类型支持

## API 配置

后端 API 通过 Vite 代理配置：

```js
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 开发指南

### 添加新组件

1. 在 `src/components/` 创建 `.vue` 文件
2. 使用 Composition API 编写逻辑
3. 在父组件中导入使用

### 添加新 API

在 `src/api/` 中添加新的 API 函数：

```js
export const newAPI = async (params) => {
  const response = await api.post('/endpoint', params)
  return response.data
}
```

### 样式定制

使用 TailwindCSS 工具类或在 `style.css` 中添加自定义样式

## 部署

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

## 常见问题

**Q: 开发服务器启动失败？**
A: 检查端口 3000 是否被占用，或在 `vite.config.js` 中修改端口

**Q: API 请求失败？**
A: 确保后端服务运行在 http://localhost:8000

**Q: 图表不显示？**
A: 检查 `chart_data` 格式是否符合 ECharts 规范

## 性能优化

- ✅ 组件懒加载
- ✅ 代码分割
- ✅ 资源压缩
- ✅ Tree-shaking

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

## License

MIT
