import axios from 'axios'
import { getSessionId } from '../utils/session'

// Always use localhost:8000/api for the API
const API_URL = 'http://localhost:8000/api'

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add session ID to all requests
apiClient.interceptors.request.use((config) => {
  const sessionId = getSessionId()
  if (sessionId && config.headers) {
    config.headers['X-Session-Id'] = sessionId
  }
  return config
})

export interface DashboardRow {
  ticker: string
  price: number
  return_7d: number
  volatility: number
  max_drawdown: number
  risk_score: number
  trend: string
  last_updated: string
}

export interface RiskDetail {
  symbol: string
  current_price: number
  market_score: number
  news_score: number
  total_score: number
  trend: string
  reasons: string[]
  ai_summary: string
  themes: string[]
  metrics: {
    return_7d: number
    volatility: number
    max_drawdown: number
  }
  price_history: Array<{
    date: string
    close: number
    volume: number
  }>
  risk_history: Array<{
    date: string
    total_score: number
    market_score: number
    news_score: number
  }>
  recent_news: Array<{
    title: string
    url: string
    published_at: string
    source: string
  }>
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  message: string
  conversation_history?: ChatMessage[]
}

export interface ChatResponse {
  message: string
  conversation_history: ChatMessage[]
}

export const api = {
  getTickers: () => apiClient.get<string[]>('/tickers'),
  addTicker: (symbol: string) => apiClient.post('/tickers', { symbol }),
  deleteTicker: (symbol: string) => apiClient.delete(`/tickers/${symbol}`),
  getDashboard: () => apiClient.get<DashboardRow[]>('/dashboard'),
  getRiskDetail: (symbol: string, period?: string) => apiClient.get<RiskDetail>(`/risk/${symbol}`, { params: period ? { period } : {} }),
  refreshAll: () => apiClient.post('/refresh'),
  refreshTicker: (symbol: string) => apiClient.post(`/refresh/${symbol}`),
  chatWithAgent: (request: ChatRequest) => apiClient.post<ChatResponse>('/agent/chat', request),
}

