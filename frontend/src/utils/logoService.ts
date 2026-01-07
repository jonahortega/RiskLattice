/**
 * Logo Service - Get company logos for stock symbols
 * Uses Finnhub logo API which provides actual company logos
 */

/**
 * Get actual company logo URL
 * Primary: Finnhub logo service (provides real company logos)
 * Fallback: TradingView logo service
 */
export function getLogoWithFallback(symbol: string): string {
  // Use TradingView logo service directly
  const lowerSymbol = symbol.toLowerCase();
  return `https://s3-symbol-logo.tradingview.com/${lowerSymbol}.svg`;
}

/**
 * Get logo URL with multiple fallback sources
 */
export function getLogoUrl(symbol: string): string {
  return getLogoWithFallback(symbol);
}
