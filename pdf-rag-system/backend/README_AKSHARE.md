# AKShare经济数据API使用指南

## 🎯 已集成的API接口

### 1. 股票实时行情
```bash
GET /api/economic/stock/realtime/{symbol}
```
**示例**: 获取比亚迪(002594)实时行情
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/economic/stock/realtime/002594
```

**返回数据**:
```json
{
  "code": "002594",
  "name": "比亚迪",
  "price": 256.80,
  "change_percent": 2.35,
  "change_amount": 5.90,
  "volume": 12345678,
  "amount": 3165432100,
  "high": 258.50,
  "low": 252.30,
  "open": 253.00,
  "close_yesterday": 250.90
}
```

### 2. 股票新闻舆情
```bash
GET /api/economic/stock/news/{symbol}?limit=10
```
**示例**: 获取比亚迪最新新闻
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/economic/stock/news/002594?limit=5
```

**返回数据**:
```json
{
  "news": [
    {
      "title": "比亚迪1月新能源汽车销量同比增长...",
      "content": "...",
      "publish_time": "2026-02-26 10:30:00",
      "source": "证券时报"
    }
  ]
}
```

### 3. 财务指标分析
```bash
GET /api/economic/stock/financial/{symbol}
```
**示例**: 获取比亚迪财务指标
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/economic/stock/financial/002594
```

**返回数据**:
```json
{
  "code": "002594",
  "report_date": "2023-12-31",
  "eps": 15.20,
  "roe": 18.50,
  "gross_profit_margin": 22.30,
  "net_profit_margin": 8.90,
  "debt_ratio": 65.20,
  "current_ratio": 1.35,
  "quick_ratio": 1.10
}
```

### 4. 股票历史行情
```bash
GET /api/economic/stock/history/{symbol}?period=daily&start_date=20240101&end_date=20240131
```
**示例**: 获取比亚迪历史行情
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/economic/stock/history/002594?period=daily&start_date=20240101&end_date=20240131"
```

### 5. 宏观经济数据 - CPI
```bash
GET /api/economic/macro/cpi
```
**返回数据**:
```json
{
  "year": "2023",
  "cpi": 102.5,
  "cpi_city": 102.8,
  "cpi_rural": 102.1
}
```

### 6. 宏观经济数据 - GDP
```bash
GET /api/economic/macro/gdp
```
**返回数据**:
```json
{
  "year": "2023",
  "gdp": 1260582.0,
  "gdp_growth": 5.2
}
```

### 7. 行业板块排名
```bash
GET /api/economic/industry/ranking
```
**返回数据**:
```json
{
  "ranking": [
    {
      "name": "新能源汽车",
      "change_percent": 3.25,
      "total_value": 2500000000000,
      "leader": "比亚迪",
      "leader_change": 4.50
    }
  ]
}
```

### 8. 股票搜索
```bash
GET /api/economic/stock/search?keyword=比亚迪
```
**返回数据**:
```json
{
  "stocks": [
    {
      "code": "002594",
      "name": "比亚迪",
      "price": 256.80,
      "change_percent": 2.35
    }
  ]
}
```

## 🚀 前端调用示例

### JavaScript/Vue示例
```javascript
// 获取股票实时行情
async function getStockRealtime(symbol) {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`http://localhost:8000/api/economic/stock/realtime/${symbol}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  const data = await response.json()
  return data
}

// 获取股票新闻
async function getStockNews(symbol, limit = 10) {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`http://localhost:8000/api/economic/stock/news/${symbol}?limit=${limit}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  const data = await response.json()
  return data.news
}

// 搜索股票
async function searchStock(keyword) {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`http://localhost:8000/api/economic/stock/search?keyword=${encodeURIComponent(keyword)}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  const data = await response.json()
  return data.stocks
}
```

## 💡 应用场景建议

### 1. 非结构化舆情溯源引擎
- 使用 `/api/economic/stock/news/{symbol}` 获取实时新闻
- 结合Dify分析新闻情感和影响

### 2. 智能企业咨询模组
- 使用 `/api/economic/stock/financial/{symbol}` 获取财务数据
- 结合AI分析企业经营状况

### 3. 全景运营评估
- 使用 `/api/economic/stock/history/{symbol}` 获取历史数据
- 使用 `/api/economic/industry/ranking` 获取行业对比
- 使用 `/api/economic/macro/cpi` 和 `/api/economic/macro/gdp` 分析宏观环境

### 4. 实时数据看板
- 使用 `/api/economic/stock/realtime/{symbol}` 实时更新股价
- 使用 `/api/economic/industry/ranking` 展示行业热点

## 📊 常用股票代码

- **比亚迪**: 002594
- **宁德时代**: 300750
- **贵州茅台**: 600519
- **中国平安**: 601318
- **招商银行**: 600036
- **五粮液**: 000858
- **美的集团**: 000333
- **格力电器**: 000651

## ⚠️ 注意事项

1. **所有API都需要JWT认证**,请先登录获取token
2. **数据来源于AKShare**,免费且实时更新
3. **股票代码格式**: A股使用6位数字代码(如002594)
4. **日期格式**: YYYYMMDD (如20240101)
5. **首次调用可能较慢**,AKShare需要从网络获取数据

## 🔄 下一步建议

1. 在前端创建**实时数据看板**组件
2. 在智能咨询中集成**实时财务数据**
3. 添加**舆情分析**功能,结合新闻API和Dify
4. 创建**行业对比**可视化图表
