import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function Welcome() {
  const navigate = useNavigate()
  const [displayedText, setDisplayedText] = useState('')
  const [showContent, setShowContent] = useState(false)
  const fullText = 'Welcome to RiskLattice.'

  useEffect(() => {
    // Typing animation
    let currentIndex = 0
    const typingInterval = setInterval(() => {
      if (currentIndex <= fullText.length) {
        setDisplayedText(fullText.slice(0, currentIndex))
        currentIndex++
      } else {
        clearInterval(typingInterval)
        // After typing completes, show the rest of the content
        setTimeout(() => setShowContent(true), 500)
      }
    }, 100) // Typing speed

    return () => clearInterval(typingInterval)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 flex items-center justify-center">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Typing Animation */}
        <div className="mb-8">
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-300 bg-clip-text text-transparent font-mono">
            {displayedText}
            <span className="animate-pulse">|</span>
          </h1>
        </div>

        {/* Content that fades in after typing */}
        {showContent && (
          <div className="animate-fade-in space-y-6">
            <p className="text-xl text-cyan-300/80 font-mono leading-relaxed">
              AI Financial Risk Intelligence Platform
            </p>
            
            <div className="mt-12 space-y-4 text-left bg-slate-900/50 backdrop-blur-sm rounded-xl border border-cyan-500/20 p-8">
              <div className="space-y-3">
                <p className="text-cyan-200/90 font-mono text-lg">
                  RiskLattice provides real-time risk analysis for financial markets, combining:
                </p>
                <ul className="space-y-2 text-cyan-300/80 font-mono">
                  <li className="flex items-start">
                    <span className="text-cyan-400 mr-3">▸</span>
                    <span>Market data analysis with volatility and drawdown metrics</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cyan-400 mr-3">▸</span>
                    <span>AI-powered news sentiment analysis</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cyan-400 mr-3">▸</span>
                    <span>Comprehensive risk scoring (0-100) with trend predictions</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cyan-400 mr-3">▸</span>
                    <span>Smart recommendations for position sizing and risk management</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-10">
              <button
                onClick={() => navigate('/home')}
                className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition-all font-mono text-lg border border-cyan-400/30 font-semibold"
              >
                Continue →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Welcome
