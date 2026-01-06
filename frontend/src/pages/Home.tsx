import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CompanyLogo } from '../components/CompanyLogo'
import { ChatAgent } from '../components/ChatAgent'
import { getSessionId } from '../utils/session'

interface MarketStock {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
}

interface MarketNews {
  title: string
  source: string
  url: string
  publishedAt: string
  summary: string
}

function Home() {
  const navigate = useNavigate()
  const [allStocks, setAllStocks] = useState<MarketStock[]>([])
  const [allNews, setAllNews] = useState<MarketNews[]>([])
  const [visibleStocks, setVisibleStocks] = useState(6)
  const [visibleNews, setVisibleNews] = useState(6)
  const [loading, setLoading] = useState(true)
  const [searchSymbol, setSearchSymbol] = useState('')
  const [searchError, setSearchError] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [addedItems, setAddedItems] = useState<MarketStock[]>([])

  // Major US stocks to display
  const majorStockSymbols = [
    // Tech Giants
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'ADBE', 'CSCO', 'AVGO',
    // Finance
    'JPM', 'BAC', 'WFC', 'V', 'MA', 'GS', 'MS',
    // Consumer & Retail
    'WMT', 'HD', 'COST', 'TGT', 'NKE', 'SBUX', 'MCD',
    // Healthcare
    'JNJ', 'PFE', 'ABBV', 'UNH', 'TMO', 'DHR', 'ABT',
    // Energy
    'XOM', 'CVX', 'SLB',
    // Industrial & Other
    'BA', 'CAT', 'GE', 'DIS', 'CMCSA', 'NFLX', 'PEP', 'KO', 'PG',
    // Emerging Tech & Growth
    'COIN', 'PLTR', 'AMD', 'INTC', 'QCOM'
  ]

  // Comprehensive list of popular stock symbols for autocomplete
  const popularStockSymbols = [
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'INTC',
    'AMD', 'CRM', 'ORCL', 'ADBE', 'CSCO', 'AVGO', 'QCOM', 'TXN', 'MU', 'AMAT',
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'V', 'MA', 'AXP', 'PYPL',
    'JNJ', 'PFE', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD', 'REGN',
    'WMT', 'HD', 'COST', 'TGT', 'LOW', 'TJX', 'DG', 'ROST', 'DLTR', 'BBY',
    'DIS', 'NFLX', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR', 'EA', 'TTWO', 'ATVI',
    'XOM', 'CVX', 'SLB', 'EOG', 'COP', 'MPC', 'VLO', 'PSX', 'OXY', 'HAL',
    'PEP', 'KO', 'SBUX', 'MCD', 'YUM', 'CMG', 'NKE', 'LULU', 'DECK', 'UAA',
    'BA', 'LMT', 'RTX', 'NOC', 'GD', 'HON', 'CAT', 'DE', 'GE', 'ETN',
    'SPY', 'QQQ', 'DIA', 'IWM', 'VTI',
    'UBER', 'LYFT', 'DASH', 'GRAB', 'ABNB', 'BKNG', 'EXPE', 'TRIP', 'TCOM', 'DESP',
    'AI', 'PLTR', 'SNOW', 'DDOG', 'CRWD', 'ZS', 'NET', 'FTNT', 'OKTA', 'S',
    'RBLX', 'U', 'HUBS', 'FROG', 'ESTC', 'DOCN', 'GTLB', 'MNDY', 'NOW', 'TEAM'
  ]


  useEffect(() => {
    loadMarketData()
    loadAddedItems()
    
    // Listen for updates when items are added/removed
    const handleMarketUpdate = () => {
      loadAddedItems()
    }
    window.addEventListener('marketItemsUpdated', handleMarketUpdate)
    
    // Fallback timeout - if loading takes more than 10 seconds, stop loading
    const timeoutId = setTimeout(() => {
      console.warn('Market data loading timeout - showing page anyway')
      setLoading(false)
    }, 10000)
    
    return () => {
      clearTimeout(timeoutId)
      window.removeEventListener('marketItemsUpdated', handleMarketUpdate)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadAddedItems = async () => {
    try {
      const addedItemsData = JSON.parse(localStorage.getItem('addedMarketItems') || '[]')
      const itemsWithData: MarketStock[] = []
      
      for (const item of addedItemsData) {
        try {
          const sessionId = getSessionId()
          const response = await fetch(`http://localhost:8000/api/market/quote/${item.symbol}`, {
            method: 'GET',
            headers: { 
              'Content-Type': 'application/json',
              'X-Session-Id': sessionId
            }
          })
          if (response && response.ok) {
            const data = await response.json()
            if (data && data.price && !data.error) {
              itemsWithData.push({
                symbol: item.symbol,
                name: item.name || item.symbol,
                price: data.price,
                change: (data.price * (data.changePercent || 0)) / 100,
                changePercent: data.changePercent || 0,
                volume: 0
              })
            }
          }
        } catch (error) {
          console.error(`Error loading added item ${item.symbol}:`, error)
        }
      }
      
      setAddedItems(itemsWithData)
    } catch (error) {
      console.error('Error loading added items:', error)
    }
  }


  const getCompanyName = (symbol: string): string => {
    const names: { [key: string]: string } = {
      // Tech Giants
      'AAPL': 'Apple Inc.',
      'MSFT': 'Microsoft Corporation',
      'GOOGL': 'Alphabet Inc.',
      'AMZN': 'Amazon.com Inc.',
      'TSLA': 'Tesla, Inc.',
      'META': 'Meta Platforms Inc.',
      'NVDA': 'NVIDIA Corporation',
      'ADBE': 'Adobe Inc.',
      'CSCO': 'Cisco Systems',
      'AVGO': 'Broadcom Inc.',
      'AMD': 'Advanced Micro Devices',
      'INTC': 'Intel Corporation',
      'QCOM': 'Qualcomm Inc.',
      'PLTR': 'Palantir Technologies',
      // Finance
      'JPM': 'JPMorgan Chase & Co.',
      'BAC': 'Bank of America',
      'WFC': 'Wells Fargo & Co.',
      'V': 'Visa Inc.',
      'MA': 'Mastercard Inc.',
      'GS': 'Goldman Sachs Group',
      'MS': 'Morgan Stanley',
      // Consumer & Retail
      'WMT': 'Walmart Inc.',
      'HD': 'Home Depot Inc.',
      'COST': 'Costco Wholesale',
      'TGT': 'Target Corporation',
      'NKE': 'Nike Inc.',
      'SBUX': 'Starbucks Corporation',
      'MCD': 'McDonald\'s Corporation',
      // Healthcare
      'JNJ': 'Johnson & Johnson',
      'PFE': 'Pfizer Inc.',
      'ABBV': 'AbbVie Inc.',
      'UNH': 'UnitedHealth Group',
      'TMO': 'Thermo Fisher Scientific',
      'DHR': 'Danaher Corporation',
      'ABT': 'Abbott Laboratories',
      // Energy
      'XOM': 'Exxon Mobil',
      'CVX': 'Chevron Corp.',
      'SLB': 'Schlumberger Limited',
      // Industrial & Other
      'BA': 'Boeing Company',
      'CAT': 'Caterpillar Inc.',
      'GE': 'General Electric',
      'DIS': 'Walt Disney Co.',
      'CMCSA': 'Comcast Corp.',
      'NFLX': 'Netflix Inc.',
      'PEP': 'PepsiCo Inc.',
      'KO': 'Coca-Cola Company',
      'PG': 'Procter & Gamble',
      // Emerging Tech
      'COIN': 'Coinbase Global'
    }
    return names[symbol] || symbol
  }

  const loadMarketData = async () => {
    setLoading(true)
    try {
      // Try dashboard endpoint first (has all watchlist stocks)
      let stocks: MarketStock[] = []
      
      try {
        // Get session ID
        const sessionId = getSessionId()
        const dashboardResponse = await fetch(`http://localhost:8000/api/dashboard`, {
          method: 'GET',
          headers: { 
            'Content-Type': 'application/json',
            'X-Session-Id': sessionId
          }
        })
        
        if (dashboardResponse && dashboardResponse.ok) {
          const dashboardData = await dashboardResponse.json()
          
          if (Array.isArray(dashboardData) && dashboardData.length > 0) {
            // Convert dashboard data to MarketStock format
            // Filter out crypto (anything with -USD, -EUR, or common crypto symbols)
            // Include indices even if price is 0
            stocks = dashboardData
              .filter((item: any) => {
                if (!item.ticker) return false
                const ticker = item.ticker.toUpperCase()
                // Exclude crypto symbols (anything with -USD, -EUR, or common crypto tickers)
                if (ticker.includes('-USD') || ticker.includes('-EUR')) return false
                const cryptoSymbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ZEC', 'BNB', 'ADA', 'DOGE', 'MATIC', 
                                      'LTC', 'AVAX', 'UNI', 'LINK', 'ATOM', 'ETC', 'XLM', 'ALGO', 
                                      'COINBASE', 'BITO', 'GBTC']
                if (cryptoSymbols.includes(ticker) || cryptoSymbols.some(c => ticker.startsWith(c))) return false
                // Only include stocks (letters only, no indices)
                return /^[A-Z]+$/.test(ticker)
              })
              .map((item: any) => {
                const price = item.price || 0
                // Calculate daily return from price points - we'll use 7-day return as fallback
                // but prefer to calculate daily from price history
                const return7d = item.return_7d || 0
                // Use daily return calculation: need to fetch from quote endpoint for accurate daily change
                let dailyChange = return7d / 7  // Rough approximation if we don't have daily data
                
                return {
                  symbol: item.ticker,
                  name: getCompanyName(item.ticker),
                  price: price,
                  change: price * (dailyChange / 100),  // Convert percentage to decimal for change amount
                  changePercent: dailyChange,
                  volume: 0
                }
              })
            console.log(`Loaded ${stocks.length} stocks from dashboard (including indices: ${stocks.filter(s => s.symbol.startsWith('^')).map(s => s.symbol).join(', ')})`)
            
            // Fetch fresh quotes for all stocks to get accurate daily change percentages
            if (stocks.length > 0) {
              console.log(`Fetching fresh quotes for ${stocks.length} stocks to get daily change percentages`)
              const quotePromises = stocks.map(async (stock) => {
                try {
                  const sessionId = getSessionId()
                  const response = await fetch(`http://localhost:8000/api/market/quote/${stock.symbol}`, {
                    method: 'GET',
                    headers: { 
                      'Content-Type': 'application/json',
                      'X-Session-Id': sessionId
                    }
                  })
                  if (response && response.ok) {
                    const data = await response.json()
                    if (data && data.price && !data.error) {
                      return {
                        symbol: stock.symbol,
                        name: stock.name,
                        price: data.price,
                        change: (data.price * (data.changePercent || 0)) / 100,
                        changePercent: data.changePercent || 0,  // This is now daily change
                        volume: 0
                      }
                    }
                  }
                } catch (error) {
                  // Return original stock data if quote fetch fails
                  return stock
                }
                return stock
              })
              
              // Update stocks with fresh quote data including daily change
              stocks = await Promise.all(quotePromises)
            }
            
            // Also fetch missing symbols from majorStockSymbols (default stocks to show)
            const dashboardTickers = new Set(stocks.map((s: MarketStock) => s.symbol))
            const missingSymbols = majorStockSymbols.filter(sym => !dashboardTickers.has(sym))
            
            if (missingSymbols.length > 0) {
              console.log(`Fetching ${missingSymbols.length} missing symbols: ${missingSymbols.join(', ')}`)
              const missingQuotePromises = missingSymbols.map(async (symbol) => {
                try {
                  const sessionId = getSessionId()
                  const response = await fetch(`http://localhost:8000/api/market/quote/${symbol}`, {
                    method: 'GET',
                    headers: { 
                      'Content-Type': 'application/json',
                      'X-Session-Id': sessionId
                    }
                  })
                  if (response && response.ok) {
                    const data = await response.json()
                    if (data && data.price && !data.error) {
                      return {
                        symbol: symbol,
                        name: getCompanyName(symbol),
                        price: data.price,
                        change: (data.price * (data.changePercent || 0)) / 100,
                        changePercent: data.changePercent || 0,  // Daily change
                        volume: 0
                      }
                    }
                  }
                } catch (error) {
                  return null
                }
                return null
              })
              
              const quoteStocks = (await Promise.all(missingQuotePromises)).filter((s): s is MarketStock => s !== null)
              stocks.push(...quoteStocks)
              console.log(`Added ${quoteStocks.length} default stocks from quotes`)
            }
          } else {
            // Dashboard returned empty array (new user with no watchlist)
            // Show default stocks from majorStockSymbols
            console.log('Dashboard is empty (new user), loading default stocks')
            stocks = []
          }
        } else {
          // Dashboard request failed, show default stocks
          console.warn('Dashboard endpoint failed, loading default stocks')
          stocks = []
        }
      } catch (error) {
        console.warn('Dashboard endpoint failed, trying individual quotes:', error)
        stocks = []
      }
      
      // If no stocks from dashboard, load default stocks from majorStockSymbols
      if (stocks.length === 0) {
        console.log('Loading default stocks from majorStockSymbols')
        const quotePromises = majorStockSymbols.slice(0, 20).map(async (symbol) => {
          try {
            const sessionId = getSessionId()
            const response = await fetch(`http://localhost:8000/api/market/quote/${symbol}`, {
              method: 'GET',
              headers: { 
                'Content-Type': 'application/json',
                'X-Session-Id': sessionId
              }
            })
            if (response && response.ok) {
              const data = await response.json()
              if (data && data.price && !data.error) {
                return {
                  symbol: symbol,
                  name: getCompanyName(symbol),
                  price: data.price,
                  change: (data.price * (data.changePercent || 0)) / 100,
                  changePercent: data.changePercent || 0,
                  volume: 0
                }
              }
            }
          } catch (error) {
            // Silently fail individual requests
            return null
          }
          return null
        })
        
        const quoteStocks = (await Promise.all(quotePromises)).filter((s): s is MarketStock => s !== null)
        stocks = quoteStocks
        console.log(`Loaded ${stocks.length} stocks from individual quotes`)
      }
      
      // Set the stocks state - THIS WAS MISSING!
      setAllStocks(stocks)
      console.log(`Total stocks set to state: ${stocks.length}`)

      // Load market news from API
      try {
        const newsResponse = await fetch(`http://localhost:8000/api/market/news?limit=30`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        })
        if (newsResponse && newsResponse.ok) {
          const newsData = await newsResponse.json()
          if (newsData && newsData.length > 0) {
            setAllNews(newsData.map((item: any) => ({
              title: item.title,
              source: item.source,
              url: item.url,
              publishedAt: item.published_at,
              summary: `${item.symbol ? `[${item.symbol}] ` : ''}${item.title}`
            })))
          } else {
            setAllNews(getPlaceholderNews())
          }
        } else {
          setAllNews(getPlaceholderNews())
        }
      } catch (error) {
        console.error('Error loading news:', error)
        setAllNews(getPlaceholderNews())
      }
    } catch (error) {
      console.error('Error loading market data:', error)
    } finally {
      // Always set loading to false, even if there are errors
      setLoading(false)
    }
  }

  const getPlaceholderNews = (): MarketNews[] => {
    const now = new Date()
    return [
      {
        title: 'Market Opens Higher as Investors Await Fed Decision',
        source: 'Financial Times',
        url: '#',
        publishedAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        summary: 'US stocks opened higher on Thursday as investors awaited the Federal Reserve\'s latest policy decision and economic projections.'
      },
      {
        title: 'Tech Stocks Rally on Strong Earnings Reports',
        source: 'Bloomberg',
        url: '#',
        publishedAt: new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString(),
        summary: 'Major technology companies posted stronger-than-expected earnings, driving a broad rally in the tech sector.'
      },
      {
        title: 'Oil Prices Surge on Supply Concerns',
        source: 'Reuters',
        url: '#',
        publishedAt: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(),
        summary: 'Oil prices climbed amid growing concerns about global supply disruptions and increasing demand.'
      },
      {
        title: 'AI Chip Demand Drives Semiconductor Stocks Higher',
        source: 'Wall Street Journal',
        url: '#',
        publishedAt: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
        summary: 'Semiconductor companies see strong demand for AI-focused chips, with NVIDIA leading gains in the sector.'
      },
      {
        title: 'Retail Sales Beat Expectations in Latest Report',
        source: 'CNBC',
        url: '#',
        publishedAt: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
        summary: 'Consumer spending remains robust as retail sales data exceeds analyst forecasts, signaling continued economic strength.'
      },
      {
        title: 'Federal Reserve Signals Potential Rate Cuts',
        source: 'Financial Times',
        url: '#',
        publishedAt: new Date(now.getTime() - 7 * 60 * 60 * 1000).toISOString(),
        summary: 'Fed officials hint at potential interest rate reductions as inflation trends downward.'
      }
    ]
  }

  const formatPrice = (price: number) => {
    if (price === 0) return 'N/A'
    // For indices, show with fewer decimals
    const decimals = price > 1000 ? 0 : 2
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(price)
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (seconds < 60) return 'Just now'
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  const showMoreStocks = () => {
    setVisibleStocks(prev => Math.min(prev + 6, allStocks.length))
  }

  const showMoreNews = () => {
    setVisibleNews(prev => Math.min(prev + 6, allNews.length))
  }

  const getSuggestions = (input: string): string[] => {
    if (!input || input.length < 1) return []
    
    const upperInput = input.toUpperCase().trim()
    // Filter symbols that start with or contain the input
    const matches = popularStockSymbols
      .filter(symbol => symbol.toUpperCase().startsWith(upperInput) || symbol.toUpperCase().includes(upperInput))
      .slice(0, 8) // Limit to 8 suggestions
    
    return matches
  }

  const handleSearchInputChange = (value: string) => {
    setSearchSymbol(value)
    setSearchError('')
    
    if (value.trim().length > 0) {
      const newSuggestions = getSuggestions(value)
      setSuggestions(newSuggestions)
      setShowSuggestions(newSuggestions.length > 0)
      setSelectedSuggestionIndex(-1)
    } else {
      setSuggestions([])
      setShowSuggestions(false)
      setSelectedSuggestionIndex(-1)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const symbol = searchSymbol.trim().toUpperCase()
    
    // If a suggestion is selected, use it
    if (selectedSuggestionIndex >= 0 && suggestions[selectedSuggestionIndex]) {
      navigateToTicker(suggestions[selectedSuggestionIndex])
      return
    }
    
    if (!symbol) {
      setSearchError('Please enter a stock symbol')
      return
    }
    
    // Remove any non-alphabetic characters except ^ for indices
    const cleanSymbol = symbol.replace(/[^A-Z^]/g, '')
    if (!cleanSymbol) {
      setSearchError('Invalid stock symbol')
      return
    }
    
    navigateToTicker(cleanSymbol)
  }

  const navigateToTicker = (symbol: string) => {
    setSearchError('')
    setSearchSymbol('')
    setSuggestions([])
    setShowSuggestions(false)
    setSelectedSuggestionIndex(-1)
    // Navigate to ticker detail page - the backend will handle fetching data if needed
    navigate(`/ticker/${symbol.toUpperCase()}`)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedSuggestionIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedSuggestionIndex(prev => (prev > 0 ? prev - 1 : -1))
        break
      case 'Enter':
        if (selectedSuggestionIndex >= 0) {
          e.preventDefault()
          navigateToTicker(suggestions[selectedSuggestionIndex])
        }
        break
      case 'Escape':
        setShowSuggestions(false)
        setSelectedSuggestionIndex(-1)
        break
    }
  }

  // Show loading state, but also allow page to render after timeout
  if (loading && allStocks.length === 0 && allNews.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-cyan-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-cyan-400 font-mono">Loading market data...</p>
        </div>
      </div>
    )
  }

  // Combine default stocks with added items
  const combinedStocks = [...allStocks, ...addedItems.filter(item => 
    !allStocks.some(stock => stock.symbol === item.symbol)
  )]

  // Display items
  const displayedItems = combinedStocks.slice(0, visibleStocks)
  const displayedNews = allNews.slice(0, visibleNews)
  const totalItems = combinedStocks.length

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/90 backdrop-blur-md border-b border-cyan-500/20 sticky top-0 z-50 shadow-lg shadow-cyan-500/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-300 bg-clip-text text-transparent font-mono tracking-tight">
                RiskLattice
              </h1>
              <p className="text-sm text-cyan-400/70 mt-1 font-mono">AI Financial Risk Intelligence</p>
            </div>
            <nav className="flex items-center space-x-4">
              <button
                onClick={() => {
                  // Open AI Assistant - this will be handled by ChatAgent component
                  const event = new CustomEvent('openChatAgent')
                  window.dispatchEvent(event)
                }}
                className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition-all font-medium font-mono border border-cyan-400/30"
              >
                AI Assistant
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* AI Assistant Chat - only visible when opened */}
      <ChatAgent />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stock Search Section */}
        <section className="mb-8">
          <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 shadow-xl shadow-cyan-500/10 p-6 relative">
            <h2 className="text-xl font-semibold mb-4 text-cyan-200 font-mono">Search Any Stock</h2>
            <form onSubmit={handleSearch} className="relative">
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={searchSymbol}
                    onChange={(e) => handleSearchInputChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => {
                      if (suggestions.length > 0) {
                        setShowSuggestions(true)
                      }
                    }}
                    onBlur={() => {
                      // Delay hiding suggestions to allow click events
                      setTimeout(() => setShowSuggestions(false), 200)
                    }}
                    placeholder="Enter stock symbol (e.g., AAPL, TSLA, MSFT)"
                    className="w-full px-4 py-3 bg-slate-800/50 border border-cyan-500/30 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-cyan-100 placeholder-cyan-400/50 font-mono text-lg"
                  />
                  
                  {/* Suggestions Dropdown */}
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute z-50 w-full mt-2 bg-slate-800 border border-cyan-500/30 rounded-lg shadow-xl shadow-cyan-500/20 overflow-hidden">
                      {suggestions.map((suggestion, index) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() => navigateToTicker(suggestion)}
                          className={`w-full px-4 py-3 text-left hover:bg-cyan-500/20 transition-colors font-mono ${
                            index === selectedSuggestionIndex
                              ? 'bg-cyan-500/30 text-cyan-100'
                              : 'text-cyan-200'
                          } ${
                            index === 0 ? '' : 'border-t border-cyan-500/10'
                          }`}
                          onMouseEnter={() => setSelectedSuggestionIndex(index)}
                        >
                          <span className="font-semibold">{suggestion}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  type="submit"
                  className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition font-medium font-mono border border-cyan-400/30"
                >
                  Search
                </button>
              </div>
            </form>
            {searchError && (
              <p className="mt-2 text-red-400 text-sm font-mono">{searchError}</p>
            )}
            <p className="mt-3 text-sm text-cyan-400/70 font-mono">
              Search for any stock symbol to view detailed risk analysis, price history, and market insights
            </p>
          </div>
        </section>

        {/* Market Overview Section */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-bold text-cyan-200 font-mono">Market Overview</h2>
            <button
              onClick={() => {
                loadMarketData()
                loadAddedItems()
              }}
              className="px-4 py-2 text-sm text-cyan-400 hover:text-cyan-300 font-medium transition border border-cyan-500/30 hover:border-cyan-500/50 rounded-lg bg-blue-950/50 hover:bg-blue-900/50 font-mono"
            >
              ↻ Refresh
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {displayedItems.map((item) => (
              <div
                key={item.symbol}
                onClick={() => navigate(`/ticker/${item.symbol}`)}
                className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 hover:border-cyan-500/40 hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-300 p-6 cursor-pointer group"
              >
                <div className="flex items-center space-x-4 mb-4">
                  <CompanyLogo symbol={item.symbol} size={56} className="rounded-xl" />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-cyan-200 group-hover:text-cyan-100 transition font-mono">
                      {item.symbol.replace('^', '')}
                    </h3>
                    <p className="text-xs text-cyan-400/60 truncate">{item.name}</p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  {item.price > 0 ? (
                    <>
                      <div className="text-2xl font-bold text-white font-mono">
                        {formatPrice(item.price)}
                      </div>
                      <div className={`text-sm font-semibold font-mono ${item.changePercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%
                      </div>
                    </>
                  ) : (
                    <div className="text-sm text-cyan-400/50 italic font-mono">
                      Loading...
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {visibleStocks < totalItems && (
            <div className="mt-8 text-center">
              <button
                onClick={showMoreStocks}
                className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition-all font-medium font-mono border border-cyan-400/30"
              >
                View More ({totalItems - visibleStocks} remaining)
              </button>
            </div>
          )}
        </section>

        {/* Market News Section */}
        <section>
          <h2 className="text-3xl font-bold text-cyan-200 mb-6 font-mono">Market News</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedNews.map((news, index) => (
              <article
                key={index}
                className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-cyan-500/20 hover:border-cyan-500/40 hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-300 overflow-hidden group"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wide font-mono">
                      {news.source}
                    </span>
                    <span className="text-xs text-cyan-400/50 font-mono">
                      {formatTimeAgo(news.publishedAt)}
                    </span>
                  </div>
                  
                  <h3 className="text-xl font-bold text-cyan-100 mb-3 group-hover:text-cyan-50 transition line-clamp-2">
                    {news.title}
                  </h3>
                  
                  <p className="text-cyan-300/70 text-sm leading-relaxed mb-4 line-clamp-3">
                    {news.summary}
                  </p>
                  
                  <a
                    href={news.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sm font-semibold text-cyan-400 hover:text-cyan-300 transition font-mono"
                  >
                    Read more →
                  </a>
                </div>
              </article>
            ))}
          </div>

          {visibleNews < allNews.length && (
            <div className="mt-8 text-center">
              <button
                onClick={showMoreNews}
                className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition-all font-medium font-mono border border-cyan-400/30"
              >
                View More ({allNews.length - visibleNews} remaining)
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default Home
