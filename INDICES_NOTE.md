# Indices Note

## Current Status:

- **NASDAQ (^IXIC)**: Active - shows first in list
- **Dow Jones (^DJI)**: Removed - caused API errors
- **S&P 500 (^GSPC)**: Removed - caused API errors

## Future:

Dow Jones and S&P 500 will be important to add back in the future when we have a better data source that supports index symbols.

## To Add Back Later:

1. Add `^DJI` and `^GSPC` back to `majorStockSymbols` array in `Home.tsx`
2. Add their names back to `getCompanyName` function
3. Add their logos back to `indexLogos` in `CompanyLogo.tsx`
4. Test with a data source that supports index symbols

