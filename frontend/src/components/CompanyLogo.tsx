import { useState, useEffect, useRef } from 'react'

interface CompanyLogoProps {
  symbol: string
  size?: number
  className?: string
}

// IMPORTANT: To get ACTUAL company logos, you need a free API key from Logo.dev
// 1. Go to: https://www.logo.dev/
// 2. Sign up for free account
// 3. Get your API token from dashboard
// 4. Add it here (or better, in an environment variable)
// For now, using placeholder until you add the token

const LOGO_DEV_TOKEN = 'pk_Vm_sYEz1QNGWK5_CwMdO-A' // Logo.dev API token for actual company logos

/**
 * Get logo URL
 */
function getLogoUrl(symbol: string): string {
  const upperSymbol = symbol.toUpperCase()
  
  // Use Logo.dev API for all stocks
  if (LOGO_DEV_TOKEN && LOGO_DEV_TOKEN.length > 0) {
    // For all stocks, use the symbol directly with Logo.dev
    const logoUrl = `https://img.logo.dev/ticker/${upperSymbol}?token=${LOGO_DEV_TOKEN}`
    console.log(`[Logo] ${upperSymbol}: Using Logo.dev API`)
    return logoUrl
  }
  
  // Fallback to placeholder if no token
  return generatePlaceholder(upperSymbol, 40)
}

function generatePlaceholder(symbol: string, size: number): string {
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#ef4444']
  const colorIndex = symbol.charCodeAt(0) % colors.length
  const bgColor = colors[colorIndex]
  
  const svgContent = `
    <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="${bgColor}" rx="6"/>
      <text x="50%" y="50%" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif" font-size="${Math.max(12, size * 0.35)}" font-weight="700" fill="white" text-anchor="middle" dominant-baseline="middle">${symbol.slice(0, 2)}</text>
    </svg>
  `.trim()
  
  return `data:image/svg+xml;base64,${btoa(svgContent)}`
}

/**
 * Company Logo Component
 * Shows actual company logos when Logo.dev token is configured
 */
export function CompanyLogo({ symbol, size = 40, className = '' }: CompanyLogoProps) {
  const [logoUrl, setLogoUrl] = useState<string>(() => getLogoUrl(symbol))
  const retryCountRef = useRef(0)

  useEffect(() => {
    setLogoUrl(getLogoUrl(symbol))
    retryCountRef.current = 0
  }, [symbol])

  const handleError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    retryCountRef.current += 1
    
    // If Logo.dev fails, use placeholder
    if (retryCountRef.current === 1) {
      const placeholder = generatePlaceholder(symbol.toUpperCase(), size)
      setLogoUrl(placeholder)
      console.log(`[Logo] ${symbol}: Logo.dev failed, using placeholder`)
    }
  }

  const handleLoad = () => {
    if (!logoUrl.startsWith('data:') && LOGO_DEV_TOKEN) {
      console.log(`[Logo] ${symbol}: ✓ Actual company logo loaded from Logo.dev!`)
    }
  }

  return (
    <img
      src={logoUrl}
      alt={`${symbol} logo`}
      className={className || `rounded object-contain bg-white p-1 border border-gray-200`}
      style={{ width: size, height: size }}
      onError={handleError}
      onLoad={handleLoad}
    />
  )
}
