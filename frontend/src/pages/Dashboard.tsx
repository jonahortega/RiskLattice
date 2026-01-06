import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, DashboardRow } from '../api/client'
import { CompanyLogo } from '../components/CompanyLogo'

function Dashboard() {
  const [tickers, setTickers] = useState<DashboardRow[]>([])
  const [loading, setLoading] = useState(true)
  const [newTicker, setNewTicker] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const response = await api.getDashboard()
      setTickers(response.data)
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddTicker = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTicker.trim()) return

    try {
      await api.addTicker(newTicker.trim().toUpperCase())
      setNewTicker('')
      await loadDashboard()
      // Trigger refresh for the new ticker
      await api.refreshTicker(newTicker.trim().toUpperCase())
      await loadDashboard()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error adding ticker')
    }
  }

  const handleDeleteTicker = async (symbol: string) => {
    if (!confirm(`Remove ${symbol} from watchlist?`)) return

    try {
      await api.deleteTicker(symbol)
      await loadDashboard()
    } catch (error) {
      console.error('Error deleting ticker:', error)
    }
  }

  const handleRefreshAll = async () => {
    setRefreshing(true)
    try {
      await api.refreshAll()
      setTimeout(() => loadDashboard(), 5000) // Wait longer for processing
    } catch (error) {
      console.error('Error refreshing:', error)
    } finally {
      setRefreshing(false)
    }
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

  const filteredTickers = tickers.filter(t =>
    t.ticker.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-300 bg-clip-text text-transparent mb-2 font-mono">
              Risk<span className="text-cyan-300">Lattice</span>
            </h1>
            <p className="text-cyan-400/70 font-mono">AI Financial Risk Intelligence Dashboard</p>
          </div>
          <button
            onClick={() => navigate('/home')}
            className="px-4 py-2 text-cyan-300 hover:text-cyan-200 hover:bg-blue-950/50 rounded-lg transition border border-cyan-500/30 hover:border-cyan-500/50 font-mono"
          >
            Market Overview
          </button>
        </div>

        <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <form onSubmit={handleAddTicker} className="flex-1 flex gap-2">
              <input
                type="text"
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                placeholder="Add ticker (e.g., AAPL, TSLA)"
                className="flex-1 px-4 py-2 bg-slate-800/50 border border-cyan-500/30 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-cyan-100 placeholder-cyan-400/50 font-mono"
              />
              <button
                type="submit"
                className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition font-mono border border-cyan-400/30"
              >
                Add
              </button>
            </form>
            <button
              onClick={handleRefreshAll}
              disabled={refreshing}
              className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 font-mono border border-cyan-400/30"
            >
              {refreshing ? 'Refreshing...' : 'Refresh All'}
            </button>
          </div>

          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search tickers..."
            className="w-full px-4 py-2 bg-slate-800/50 border border-cyan-500/30 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-cyan-100 placeholder-cyan-400/50 font-mono"
          />
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-2 border-cyan-500 border-t-transparent"></div>
            <p className="mt-4 text-cyan-400 font-mono">Loading dashboard...</p>
          </div>
        ) : filteredTickers.length === 0 ? (
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-12 text-center">
            <p className="text-cyan-300/70 text-lg font-mono">
              {searchTerm ? 'No tickers match your search.' : 'No tickers in watchlist. Add one to get started!'}
            </p>
          </div>
        ) : (
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-cyan-500/20">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Ticker
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      7D Return
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Volatility
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Max Drawdown
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Risk Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Trend
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Last Updated
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-cyan-400 uppercase tracking-wider font-mono">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-slate-900/50 divide-y divide-cyan-500/10">
                  {filteredTickers.map((row) => (
                    <tr key={row.ticker} className="hover:bg-slate-800/50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-3">
                          <CompanyLogo symbol={row.ticker} size={40} className="rounded object-contain bg-slate-800/50 p-1 border border-cyan-500/20" />
                          <button
                            onClick={() => navigate(`/ticker/${row.ticker}`)}
                            className="text-cyan-300 hover:text-cyan-200 font-semibold hover:underline transition font-mono"
                          >
                            {row.ticker}
                          </button>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-mono">
                        ${row.price.toFixed(2)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium font-mono ${
                        row.return_7d >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {row.return_7d >= 0 ? '+' : ''}{row.return_7d.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-cyan-200 font-mono">
                        {row.volatility.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-cyan-200 font-mono">
                        {row.max_drawdown.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold font-mono ${
                          row.risk_score <= 40 
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                            : row.risk_score <= 70 
                            ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' 
                            : 'bg-red-500/20 text-red-400 border border-red-500/30'
                        }`}>
                          {row.risk_score.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-cyan-300">
                        {getTrendIcon(row.trend)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-cyan-400/70 font-mono text-xs">
                        {new Date(row.last_updated).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleDeleteTicker(row.ticker)}
                          className="text-red-400 hover:text-red-300 hover:underline transition font-mono"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard

