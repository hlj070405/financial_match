const BASE_URL = '/api/tushare'
const WATCHLIST_URL = '/api/watchlist'

function getHeaders() {
  const token = localStorage.getItem('access_token')
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
}

async function request(path, params = {}) {
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&')
  const url = `${BASE_URL}${path}${qs ? '?' + qs : ''}`
  const res = await fetch(url, { headers: getHeaders() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const tushareApi = {
  testConnection: () => request('/test'),

  getStockBasic: (exchange = '', list_status = 'L') =>
    request('/stock_basic', { exchange, list_status }),

  getTradeCalendar: (exchange = 'SSE', start_date, end_date) =>
    request('/trade_cal', { exchange, start_date, end_date }),

  getDaily: (ts_code, start_date, end_date) =>
    request(`/daily/${ts_code}`, { start_date, end_date }),

  getDailyBasic: (ts_code = '', trade_date = '') =>
    request('/daily_basic', { ts_code, trade_date }),

  getWeekly: (ts_code, start_date, end_date) =>
    request(`/weekly/${ts_code}`, { start_date, end_date }),

  getMonthly: (ts_code, start_date, end_date) =>
    request(`/monthly/${ts_code}`, { start_date, end_date }),

  getIndexBasic: (market = '', limit = 20) =>
    request('/index_basic', { market, limit }),

  getIndexDaily: (ts_code, start_date, end_date) =>
    request(`/index_daily/${ts_code}`, { start_date, end_date }),

  getMoneyflow: (ts_code, start_date, end_date) =>
    request(`/moneyflow/${ts_code}`, { start_date, end_date }),

  getBalancesheet: (ts_code, period = '', limit = 4) =>
    request(`/balancesheet/${ts_code}`, { period, limit }),

  getCashflow: (ts_code, period = '', limit = 4) =>
    request(`/cashflow/${ts_code}`, { period, limit }),
}

export const watchlistApi = {
  list: async () => {
    const res = await fetch(WATCHLIST_URL, { headers: getHeaders() })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  add: async (ts_code, name) => {
    const res = await fetch(WATCHLIST_URL, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ ts_code, name })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  },

  remove: async (ts_code) => {
    const res = await fetch(`${WATCHLIST_URL}/${encodeURIComponent(ts_code)}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
}
