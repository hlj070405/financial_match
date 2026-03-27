const BASE_URL = '/api/tushare'
const WATCHLIST_URL = '/api/watchlist'
const REQUEST_TIMEOUT_MS = 12000

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

  let lastError = null
  for (let i = 0; i < 2; i += 1) {
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), REQUEST_TIMEOUT_MS)
    try {
      const res = await fetch(url, { headers: getHeaders(), signal: ctrl.signal })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return await res.json()
    } catch (err) {
      lastError = err
      if (i === 1) break
    } finally {
      clearTimeout(timer)
    }
  }

  const msg = lastError?.name === 'AbortError' ? 'Request timeout' : (lastError?.message || 'Request failed')
  throw new Error(msg)
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

export const agentApi = {
  analyze: async (stock_name, ts_code) => {
    const res = await fetch('/api/agent/analyze', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ stock_name, ts_code })
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  status: async (ts_code) => {
    const res = await fetch(`/api/agent/status/${encodeURIComponent(ts_code)}`, {
      headers: getHeaders()
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  clearCache: async (ts_code) => {
    const res = await fetch(`/api/agent/cache/${encodeURIComponent(ts_code)}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  followup: async (stock_name, ts_code, question, context = '') => {
    const res = await fetch('/api/agent/followup', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ stock_name, ts_code, question, context })
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  analyzeStream: (stock_name, ts_code, { onPhase, onDelta, onDone, onError }) => {
    const ctrl = new AbortController()
    fetch('/api/agent/analyze_stream', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ stock_name, ts_code }),
      signal: ctrl.signal,
    }).then(async (res) => {
      if (!res.ok) {
        onError?.(`HTTP ${res.status}`)
        return
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop()
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || !trimmed.startsWith('data: ')) continue
          const payload = trimmed.slice(6)
          if (payload === '[DONE]') {
            onDone?.()
            return
          }
          try {
            const evt = JSON.parse(payload)
            if (evt.type === 'phase') onPhase?.(evt.content)
            else if (evt.type === 'delta') onDelta?.(evt.content)
            else if (evt.type === 'done') onDone?.()
            else if (evt.type === 'error') onError?.(evt.content)
          } catch {}
        }
      }
      onDone?.()
    }).catch((err) => {
      if (err.name !== 'AbortError') onError?.(err.message)
    })
    return ctrl
  }
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
