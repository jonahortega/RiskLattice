import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { api, RiskDetail } from '../api/client'
import { CompanyLogo } from '../components/CompanyLogo'

type TimePeriod = '1d' | '1m' | '90d' | '6m' | '1y' | '5y'

function TickerDetail() {
  const { symbol } = useParams<{ symbol: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<RiskDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [isAdded, setIsAdded] = useState(false)
  const [pricePeriod, setPricePeriod] = useState<TimePeriod>('90d')

  useEffect(() => {
    if (symbol) {
      checkIfAdded()
    }
  }, [symbol])

  const checkIfAdded = async () => {
    if (!symbol) return
    
    // Check localStorage
    const addedItems = JSON.parse(localStorage.getItem('addedMarketItems') || '[]')
    const inLocalStorage = addedItems.some((item: { symbol: string }) => item.symbol === symbol.toUpperCase())
    
    // Also check backend watchlist
    try {
      const response = await api.getTickers()
      const tickers = response.data
      const inBackend = tickers.includes(symbol.toUpperCase())
      setIsAdded(inLocalStorage || inBackend)
    } catch (error) {
      // If backend check fails, use localStorage
      setIsAdded(inLocalStorage)
    }
  }

  const handleAddToMarket = async () => {
    if (!symbol || !data) return
    
    try {
      // Add to backend watchlist (user-specific)
      await api.addTicker(symbol.toUpperCase())
      
      // Also add to localStorage for frontend display
      const addedItems = JSON.parse(localStorage.getItem('addedMarketItems') || '[]')
      const itemExists = addedItems.some((item: { symbol: string }) => item.symbol === symbol.toUpperCase())
      
      if (!itemExists) {
        const newItem = {
          symbol: symbol.toUpperCase(),
          name: data.symbol,
          price: data.current_price,
          changePercent: data.metrics.return_7d || 0,
          type: 'stock'
        }
        addedItems.push(newItem)
        localStorage.setItem('addedMarketItems', JSON.stringify(addedItems))
      }
      
      setIsAdded(true)
      
      // Dispatch event to refresh market overview
      window.dispatchEvent(new CustomEvent('marketItemsUpdated'))
    } catch (error) {
      console.error('Error adding to market:', error)
      // Still update localStorage even if backend fails
      const addedItems = JSON.parse(localStorage.getItem('addedMarketItems') || '[]')
      const itemExists = addedItems.some((item: { symbol: string }) => item.symbol === symbol.toUpperCase())
      if (!itemExists) {
        const newItem = {
          symbol: symbol.toUpperCase(),
          name: data.symbol,
          price: data.current_price,
          changePercent: data.metrics.return_7d || 0,
          type: 'stock'
        }
        addedItems.push(newItem)
        localStorage.setItem('addedMarketItems', JSON.stringify(addedItems))
        setIsAdded(true)
        window.dispatchEvent(new CustomEvent('marketItemsUpdated'))
      }
    }
  }

  const handleRemoveFromMarket = () => {
    if (!symbol) return
    
    const addedItems = JSON.parse(localStorage.getItem('addedMarketItems') || '[]')
    const filtered = addedItems.filter((item: { symbol: string }) => item.symbol !== symbol.toUpperCase())
    localStorage.setItem('addedMarketItems', JSON.stringify(filtered))
    setIsAdded(false)
    
    // Dispatch event to refresh market overview
    window.dispatchEvent(new CustomEvent('marketItemsUpdated'))
  }

  const loadDetail = async () => {
    if (!symbol) return
    try {
      setLoading(true)
      const response = await api.getRiskDetail(symbol, pricePeriod)
      if (response.data) {
        setData(response.data)
        setLoading(false)
      } else {
        console.error('No data in response, attempting to fetch...')
        // Try refreshing the ticker data and reload
        try {
          await api.refreshTicker(symbol)
          // Wait a bit for processing, then retry
          console.log('Waiting for data to process...')
          setTimeout(async () => {
            try {
              setLoading(true)
              const retryResponse = await api.getRiskDetail(symbol, pricePeriod)
              if (retryResponse.data) {
                setData(retryResponse.data)
              }
            } catch (retryError) {
              console.error('Retry also failed:', retryError)
            } finally {
              setLoading(false)
            }
          }, 8000) // Wait 8 seconds for data processing (increased from 5)
        } catch (refreshError) {
          console.error('Error refreshing ticker:', refreshError)
          setLoading(false)
        }
      }
    } catch (error: any) {
      console.error('Error loading detail:', error)
      // If error, try to refresh data and retry once
      if (error?.response?.status === 404 || error?.response?.status === 500) {
        try {
          console.log('Ticker not found or error occurred, attempting to fetch data...')
          setLoading(true) // Keep loading state during refresh
          await api.refreshTicker(symbol)
          // Wait for processing (give it more time for full processing)
          console.log('Waiting for data processing to complete...')
          setTimeout(async () => {
            try {
              const retryResponse = await api.getRiskDetail(symbol, pricePeriod)
              if (retryResponse.data) {
                setData(retryResponse.data)
              } else {
                console.error('Still no data after retry')
              }
            } catch (retryError: any) {
              console.error('Retry also failed:', retryError)
              if (retryError?.response?.status === 404) {
                // Show error message to user
                console.error(`Could not load data for ${symbol}. The stock may not exist or data is still processing.`)
              }
            } finally {
              setLoading(false)
            }
          }, 10000) // Wait 10 seconds for full data processing
        } catch (refreshError) {
          console.error('Error refreshing ticker:', refreshError)
          setLoading(false)
        }
      } else {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    if (symbol && pricePeriod) {
      loadDetail()
    }
  }, [symbol, pricePeriod])

  const handleRefresh = async () => {
    if (!symbol) return
    setRefreshing(true)
    try {
      await api.refreshTicker(symbol)
      setTimeout(() => loadDetail(), 2000)
    } catch (error) {
      console.error('Error refreshing:', error)
    } finally {
      setRefreshing(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-2 border-cyan-500 border-t-transparent"></div>
          <p className="mt-4 text-cyan-400 font-mono">Loading...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-cyan-300 mb-4 font-mono">No data available</p>
          <button
            onClick={() => navigate('/home')}
            className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition font-mono border border-cyan-400/30"
          >
            Back to Market Overview
          </button>
        </div>
      </div>
    )
  }

  const priceChartData = data.price_history.map(p => ({
    date: formatDate(p.date),
    price: p.close,
    volume: p.volume
  }))

  const riskChartData = data.risk_history.map(r => ({
    date: formatDate(r.date),
    total: r.total_score,
    market: r.market_score,
    news: r.news_score
  }))

  const getRiskColor = (score: number) => {
    if (score >= 70) return 'text-red-400'
    if (score >= 40) return 'text-yellow-400'
    return 'text-green-400'
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return '↗️'
      case 'down':
        return '↘️'
      case 'flat':
        return '→'
      default:
        return '🆕'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <button
                onClick={() => navigate('/home')}
                className="text-cyan-400 hover:text-cyan-300 mb-2 block font-mono border border-cyan-500/30 hover:border-cyan-500/50 px-3 py-1 rounded-lg bg-blue-950/50 hover:bg-blue-900/50 transition"
              >
                ← Back to Market Overview
              </button>
              <div className="flex items-center space-x-4">
                <CompanyLogo symbol={data.symbol} size={64} className="rounded-lg object-contain bg-slate-800/50 p-2 border border-cyan-500/20" />
                <div>
                  <h1 className="text-4xl font-bold text-cyan-200 font-mono">{data.symbol}</h1>
                  <p className="text-cyan-400/70 mt-1 font-mono">Current Price: ${data.current_price.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {isAdded ? (
              <button
                onClick={handleRemoveFromMarket}
                className="px-6 py-2 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg hover:shadow-lg hover:shadow-red-500/50 transition font-mono border border-red-400/30"
              >
                Remove from Market
              </button>
            ) : (
              <button
                onClick={handleAddToMarket}
                className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:shadow-lg hover:shadow-green-500/50 transition font-mono border border-green-400/30"
              >
                Add to Market
              </button>
            )}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 font-mono border border-cyan-400/30"
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Risk Score Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6">
            <p className="text-sm text-cyan-400/70 mb-1 font-mono">Total Risk Score</p>
            <p className={`text-3xl font-bold font-mono ${getRiskColor(data.total_score)}`}>
              {data.total_score.toFixed(1)}
            </p>
            <p className="text-sm text-cyan-400/50 mt-2 font-mono">Trend: {getTrendIcon(data.trend)}</p>
          </div>
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6">
            <p className="text-sm text-cyan-400/70 mb-1 font-mono">Market Risk</p>
            <p className={`text-3xl font-bold font-mono ${getRiskColor(data.market_score)}`}>
              {data.market_score.toFixed(1)}
            </p>
          </div>
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6">
            <p className="text-sm text-cyan-400/70 mb-1 font-mono">News Risk</p>
            <p className={`text-3xl font-bold font-mono ${getRiskColor(data.news_score)}`}>
              {data.news_score.toFixed(1)}
            </p>
          </div>
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6">
            <p className="text-sm text-cyan-400/70 mb-1 font-mono">7D Return</p>
            <p className={`text-3xl font-bold font-mono ${
              data.metrics.return_7d >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {data.metrics.return_7d >= 0 ? '+' : ''}{data.metrics.return_7d.toFixed(2)}%
            </p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-cyan-200 font-mono">
                Price History ({pricePeriod === '1d' ? '1 Day' : pricePeriod === '1m' ? '1 Month' : pricePeriod === '90d' ? '90 Days' : pricePeriod === '6m' ? '6 Months' : pricePeriod === '1y' ? '1 Year' : '5 Years'})
              </h2>
              <div className="flex gap-2 flex-wrap">
                {(['1d', '1m', '90d', '6m', '1y', '5y'] as TimePeriod[]).map((period) => {
                  const labels: Record<TimePeriod, string> = {
                    '1d': '1 Day',
                    '1m': '1 Month',
                    '90d': '90 Days',
                    '6m': '6 Months',
                    '1y': '1 Year',
                    '5y': '5 Years'
                  }
                  return (
                    <button
                      key={period}
                      onClick={() => setPricePeriod(period)}
                      className={`px-3 py-1 rounded-lg text-sm font-mono border transition ${
                        pricePeriod === period
                          ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white border-cyan-400/30'
                          : 'bg-slate-800/50 text-cyan-300 border-cyan-500/20 hover:border-cyan-500/40'
                      }`}
                    >
                      {labels[period]}
                    </button>
                  )
                })}
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={priceChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#0ea5e9" strokeOpacity={0.2} />
                <XAxis dataKey="date" stroke="#22d3ee" />
                <YAxis stroke="#22d3ee" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #06b6d4', color: '#e0f2fe' }} />
                <Legend />
                <Area type="monotone" dataKey="price" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6">
            <h2 className="text-xl font-semibold mb-4 text-cyan-200 font-mono">Risk Score History (90 Days)</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={riskChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#0ea5e9" strokeOpacity={0.2} />
                <XAxis dataKey="date" stroke="#22d3ee" />
                <YAxis domain={[0, 100]} stroke="#22d3ee" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #06b6d4', color: '#e0f2fe' }} />
                <Legend />
                <Area type="monotone" dataKey="total" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
                <Area type="monotone" dataKey="market" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                <Area type="monotone" dataKey="news" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Analysis */}
        <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-cyan-200 font-mono">AI Analysis</h2>
          <p className="text-cyan-300/90 mb-4">{data.ai_summary}</p>
          {data.themes.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-cyan-400/70 mb-2 font-mono">Risk Themes:</p>
              <div className="flex flex-wrap gap-2">
                {data.themes.map((theme, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm border border-red-500/30 font-mono"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Risk Reasons */}
        <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-cyan-200 font-mono">Risk Factors</h2>
          <ul className="space-y-2">
            {data.reasons.map((reason, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-cyan-400 mr-2">▸</span>
                <span className="text-cyan-300/90">{reason}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Market Metrics */}
        <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-cyan-200 font-mono">Market Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-cyan-400/70 font-mono">Volatility (Annualized)</p>
              <p className="text-2xl font-semibold text-cyan-200 font-mono">{data.metrics.volatility.toFixed(2)}%</p>
            </div>
            <div>
              <p className="text-sm text-cyan-400/70 font-mono">Max Drawdown</p>
              <p className="text-2xl font-semibold text-cyan-200 font-mono">{data.metrics.max_drawdown.toFixed(2)}%</p>
            </div>
            <div>
              <p className="text-sm text-cyan-400/70 font-mono">7-Day Return</p>
              <p className={`text-2xl font-semibold font-mono ${
                data.metrics.return_7d >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {data.metrics.return_7d >= 0 ? '+' : ''}{data.metrics.return_7d.toFixed(2)}%
              </p>
            </div>
          </div>
        </div>

        {/* Recent News */}
        <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6">
          <h2 className="text-xl font-semibold mb-4 text-cyan-200 font-mono">Recent News</h2>
          {data.recent_news.length === 0 ? (
            <p className="text-cyan-400/70 font-mono">No recent news available.</p>
          ) : (
            <div className="space-y-4">
              {data.recent_news.map((article, idx) => (
                <div key={idx} className="border-b border-cyan-500/20 pb-4 last:border-0">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-300 hover:text-cyan-200 font-medium block mb-1 transition"
                  >
                    {article.title}
                  </a>
                  <p className="text-sm text-cyan-400/60 font-mono">
                    {article.source} • {formatDate(article.published_at)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TickerDetail

