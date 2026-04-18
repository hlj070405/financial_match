const BASE_URL = '/api/backtest'

function getHeaders() {
  const token = localStorage.getItem('access_token')
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
}

export const backtestApi = {
  getStrategies: async () => {
    const res = await fetch(`${BASE_URL}/strategies`, { headers: getHeaders() })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  run: async (params) => {
    const res = await fetch(`${BASE_URL}/run`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(params)
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  }
}

const PORTFOLIO_URL = '/api/portfolio'

export const portfolioApi = {
  trade: async (params) => {
    const res = await fetch(`${PORTFOLIO_URL}/trade`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(params)
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  },

  getPositions: async () => {
    const res = await fetch(`${PORTFOLIO_URL}/positions`, { headers: getHeaders() })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  getTransactions: async (limit = 50) => {
    const res = await fetch(`${PORTFOLIO_URL}/transactions?limit=${limit}`, { headers: getHeaders() })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
}
