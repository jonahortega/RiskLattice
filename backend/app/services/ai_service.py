import json
import os
from typing import Dict, List, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.core.config import settings
from app.models.models import NewsArticle


class AIService:
    def __init__(self):
        self.openai_key = settings.openai_api_key
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze_news(self, articles: List[NewsArticle], market_data: Optional[Dict] = None) -> Dict:
        """Analyze news articles with market context and return sentiment, themes, and summary."""
        if self.openai_key:
            return self._analyze_with_llm(articles, market_data)
        else:
            return self._analyze_with_fallback(articles, market_data)
    
    def _analyze_with_llm(self, articles: List[NewsArticle], market_data: Optional[Dict] = None) -> Dict:
        """Use OpenAI to analyze news with market context."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            
            headlines = [{"title": a.title, "url": a.url} for a in articles[:15]]
            headlines_text = "\n".join([f"- {h['title']}" for h in headlines])
            
            # Build market context
            market_context = ""
            if market_data:
                price_change = market_data.get('return_7d', 0)
                volatility = market_data.get('vol_ann', 0)
                drawdown = market_data.get('max_drawdown', 0)
                current_price = market_data.get('price', 0)
                
                price_direction = "DOWN" if price_change < -2 else "UP" if price_change > 2 else "FLAT"
                volatility_status = "HIGH" if volatility > 30 else "MODERATE" if volatility > 20 else "LOW"
                
                market_context = f"""

CURRENT MARKET CONDITIONS (RIGHT NOW):
- Price Movement: {price_direction} ({price_change:+.2f}% over 7 days)
- Current Price: ${current_price:.2f}
- Volatility: {volatility_status} ({volatility:.1f}% annualized)
- Max Drawdown: {drawdown:.2f}%
- Market Trend: {'BEARISH' if price_change < -3 and volatility > 25 else 'BULLISH' if price_change > 3 and volatility < 20 else 'MIXED'}
"""
            
            prompt = f"""You are a financial risk analyst. Analyze the CURRENT market situation RIGHT NOW.

{market_context}

RECENT NEWS HEADLINES:
{headlines_text}

Provide a DIRECT, ACTIONABLE analysis. Return ONLY valid JSON:
{{
    "sentiment": <float from -1.0 to 1.0, where -1.0 is very negative/bearish, 1.0 is very positive/bullish>,
    "themes": [<array of 3-5 key themes like "earnings concern", "regulatory risk", "volatility spike", "positive momentum", "market selloff", etc.>],
    "summary": "<2-3 sentence DIRECT summary. Start with 'Currently...' or 'Right now...' Be specific about what's happening NOW. Combine news sentiment with actual price movement. Example: 'Currently, the stock is down 5% amid negative earnings news and regulatory concerns, indicating bearish momentum.'",
    "market_outlook": "<ONE WORD: 'POSITIVE', 'NEGATIVE', or 'NEUTRAL' based on BOTH news AND price movement>",
    "headline_impacts": [
        {{"title": "<headline>", "impact": <int from -2 to 2>, "reason": "<why this matters right now>"}}
    ]
}}

CRITICAL RULES:
- Be DIRECT and CURRENT - focus on what's happening RIGHT NOW
- Combine news sentiment with actual price movement
- If price is DOWN and news is negative = STRONGLY NEGATIVE
- If price is UP but news is mixed = NEUTRAL to slightly positive
- Market outlook must reflect BOTH news AND price action together
- Summary must be active voice, present tense, specific

Return ONLY valid JSON, no markdown formatting."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial risk analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            
            # Validate and normalize
            sentiment = float(result.get("sentiment", 0))
            themes = result.get("themes", [])
            summary = result.get("summary", "No summary available.")
            headline_impacts = result.get("headline_impacts", [])
            market_outlook = result.get("market_outlook", "NEUTRAL")
            
            # Ensure summary starts with active language if it doesn't
            if not summary.startswith(("Currently", "Currently,", "Right now", "Right now,", "The stock", "The market")):
                if market_data:
                    price_change = market_data.get('return_7d', 0)
                    if price_change < -2:
                        summary = f"Currently, {summary.lower()}"
                    elif price_change > 2:
                        summary = f"Right now, {summary.lower()}"
                    else:
                        summary = f"The stock {summary.lower()}"
            
            return {
                "sentiment": max(-1, min(1, sentiment)),
                "themes": themes[:5],  # Limit to 5 themes
                "summary": summary,
                "market_outlook": market_outlook,
                "headline_impacts": headline_impacts[:15],
                "raw_json": json.dumps(result)
            }
        except Exception as e:
            print(f"LLM analysis failed: {e}, falling back to sentiment analysis")
            return self._analyze_with_fallback(articles)
    
    def _analyze_with_fallback(self, articles: List[NewsArticle], market_data: Optional[Dict] = None) -> Dict:
        """Use VADER sentiment analysis as fallback with market context."""
        if not articles:
            outlook = "NEUTRAL"
            summary = "Currently, no recent news available to analyze."
            if market_data:
                price_change = market_data.get('return_7d', 0)
                if price_change < -2:
                    outlook = "NEGATIVE"
                    summary = f"Currently, no news available but stock is down {price_change:.1f}%, indicating negative momentum."
                elif price_change > 2:
                    outlook = "POSITIVE"
                    summary = f"Right now, no news available but stock is up {price_change:.1f}%, showing positive momentum."
            
            return {
                "sentiment": 0.0,
                "themes": [],
                "summary": summary,
                "market_outlook": outlook,
                "headline_impacts": [],
                "raw_json": "{}"
            }
        
        sentiments = []
        headline_impacts = []
        risk_keywords = ["lawsuit", "regulation", "investigation", "decline", "loss", "miss", "warning", "breach", "fraud", "selloff", "crash", "drop"]
        positive_keywords = ["growth", "profit", "gain", "beat", "surge", "rally", "upgrade", "soar", "jump", "rise"]
        
        for article in articles[:15]:
            scores = self.analyzer.polarity_scores(article.title)
            compound = scores['compound']
            sentiments.append(compound)
            
            # Determine impact
            title_lower = article.title.lower()
            impact = compound
            reason = "Sentiment analysis"
            
            if any(kw in title_lower for kw in risk_keywords):
                impact = min(impact - 0.3, -2.0)
                reason = "Contains risk keywords"
            elif any(kw in title_lower for kw in positive_keywords):
                impact = max(impact + 0.3, 2.0)
                reason = "Contains positive keywords"
            
            headline_impacts.append({
                "title": article.title,
                "impact": max(-2, min(2, impact)),
                "reason": reason
            })
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # Extract themes
        themes = []
        all_text = " ".join([a.title.lower() for a in articles])
        for keyword in risk_keywords:
            if keyword in all_text:
                themes.append(keyword)
        
        # Build active summary with market context
        sentiment_word = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
        
        if market_data:
            price_change = market_data.get('return_7d', 0)
            volatility = market_data.get('vol_ann', 0)
            
            if price_change < -2 and avg_sentiment < -0.1:
                summary = f"Currently, the stock is down {price_change:.1f}% amid {sentiment_word} news sentiment, indicating bearish momentum. High volatility ({volatility:.1f}%) suggests continued uncertainty."
                outlook = "NEGATIVE"
            elif price_change > 2 and avg_sentiment > 0.1:
                summary = f"Right now, the stock is up {price_change:.1f}% with {sentiment_word} news sentiment, showing bullish momentum. Market conditions appear favorable."
                outlook = "POSITIVE"
            elif price_change < -2:
                summary = f"Currently, the stock is down {price_change:.1f}% despite {sentiment_word} news, indicating mixed signals. Monitor for trend continuation."
                outlook = "NEGATIVE" if price_change < -3 else "NEUTRAL"
            elif price_change > 2:
                summary = f"Right now, the stock is up {price_change:.1f}% with {sentiment_word} news sentiment, showing positive momentum."
                outlook = "POSITIVE"
            else:
                summary = f"Currently, {sentiment_word} news sentiment with {price_change:+.1f}% price movement. Market conditions are relatively stable."
                outlook = "NEUTRAL"
        else:
            summary = f"Currently, analyzed {len(articles)} headlines showing {sentiment_word} sentiment overall."
            outlook = "POSITIVE" if avg_sentiment > 0.1 else "NEGATIVE" if avg_sentiment < -0.1 else "NEUTRAL"
        
        return {
            "sentiment": max(-1, min(1, avg_sentiment)),
            "themes": themes[:5],
            "summary": summary,
            "market_outlook": outlook,
            "headline_impacts": headline_impacts,
            "raw_json": json.dumps({"method": "vader", "sentiment": avg_sentiment, "themes": themes, "outlook": outlook})
        }
    
    def chat(self, user_message: str, context_data: Optional[Dict] = None, conversation_history: Optional[List] = None) -> str:
        """Handle general financial and stock-related questions with market context."""
        if self.openai_key:
            return self._chat_with_llm(user_message, context_data, conversation_history)
        else:
            return self._chat_fallback(user_message, context_data)
    
    def _chat_with_llm(self, user_message: str, context_data: Optional[Dict] = None, conversation_history: Optional[List] = None) -> str:
        """Use OpenAI to answer financial/stock questions with context."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            
            # Build context from database
            context_text = ""
            if context_data:
                watchlist = context_data.get('watchlist', [])
                market_summary = context_data.get('market_summary', {})
                recent_news = context_data.get('recent_news', [])
                forecasts = context_data.get('forecasts', [])
                
                if watchlist:
                    if is_prediction_question:
                        context_text += "\n\n=== CURRENT STOCK PRICES (CRITICAL FOR PRICE PREDICTIONS) ===\n"
                        context_text += "Use these CURRENT PRICES as the baseline for your predictions. Calculate future prices from here.\n\n"
                    else:
                        context_text += "\n\n=== CURRENT WATCHLIST DATA (Use this for stock questions) ===\n"
                    
                    for ticker in watchlist[:20]:  # Include more tickers
                        symbol = ticker.get('symbol', '')
                        price = ticker.get('price', 0)
                        risk = ticker.get('risk_score', 0)
                        return_7d = ticker.get('return_7d', 0)
                        vol = ticker.get('volatility', 0)
                        drawdown = ticker.get('max_drawdown', 0)
                        context_text += f"**{symbol}**: Current Price=${price:.2f}, Risk Score={risk:.1f}/100, 7D Return={return_7d:+.2f}%, Volatility={vol:.1f}%, Max Drawdown={drawdown:.2f}%\n"
                    
                    if is_prediction_question:
                        context_text += "\n**IMPORTANT FOR PREDICTIONS:** If predicting for a stock above, calculate future prices from the CURRENT PRICE listed. For example, if AAPL is $271, predict 5-year target from $271 (e.g., $350-400, $400-450, etc.).\n"
                    elif is_market_wide_question:
                        context_text += "\n**IMPORTANT FOR MARKET-WIDE QUESTIONS:** If the user asks about 'most bullish stocks', 'best stocks', 'top performers', etc., analyze ALL stocks above and rank them based on:\n"
                        context_text += "- HIGHEST 7-day returns (most positive)\n"
                        context_text += "- LOWEST risk scores (safest)\n"
                        context_text += "- POSITIVE price trends\n"
                        context_text += "- LOW volatility (more stable)\n"
                        context_text += "Provide a ranked list with top 5-10 stocks and explain why each is bullish. Include their metrics (price, return, risk score, volatility).\n"
                    else:
                        context_text += "\nIf a user asks about a stock in this watchlist, USE THIS DATA in your response.\n"
                
                if market_summary:
                    context_text += f"\nMARKET OVERVIEW:\n- Total tickers tracked: {market_summary.get('total_tickers', 0)}\n"
                    avg_risk = market_summary.get('avg_risk_score', 0)
                    if avg_risk:
                        context_text += f"- Average risk score: {avg_risk:.1f}\n"
                
                # Include recent news articles for stock/news questions
                if recent_news:
                    context_text += f"\n\n=== RECENT MARKET NEWS (Last 7 Days) ===\n"
                    context_text += "Use these articles to provide current context and cite as sources:\n\n"
                    for article in recent_news[:25]:  # Include more articles
                        symbol = article.get('symbol', 'N/A')
                        title = article.get('title', '')
                        source = article.get('source', 'Unknown')
                        url = article.get('url', '')
                        published = article.get('published_at', '')[:10] if article.get('published_at') else 'N/A'
                        context_text += f"**[{symbol}]** {title}\n   - Source: {source} | Published: {published}\n   - URL: {url}\n\n"
                
                # Include risk forecasts for prediction questions
                if forecasts:
                    context_text += f"\n\nRISK FORECASTS (Predictions):\n"
                    for forecast in forecasts[:10]:
                        symbol = forecast.get('symbol', 'N/A')
                        predicted_score = forecast.get('predicted_score', 0)
                        confidence = forecast.get('confidence', 0)
                        forecast_date = forecast.get('forecast_date', '')[:10] if forecast.get('forecast_date') else 'N/A'
                        context_text += f"- {symbol}: Predicted risk score {predicted_score:.1f} (Confidence: {confidence:.1f}%, Forecast date: {forecast_date})\n"
            
            # Customize prompt based on question type
            if is_prediction_question:
                system_prompt = """You are an expert financial advisor AI assistant for RiskLattice. The user is asking for a PRICE PREDICTION - provide SPECIFIC PRICE TARGETS with dollar amounts, NOT vague statements.

CRITICAL CONTEXT UNDERSTANDING RULES:
1. **ALWAYS check conversation history** - If the user asks "give me a 5 year prediction" or "will it rise?" without mentioning a stock name, you MUST look at previous messages to find which stock they're discussing
2. **NEVER give generic responses** - If asked about a specific stock or company, ALWAYS provide a detailed, substantive answer using available data
3. **Use ALL available context** - Check the watchlist data, news articles, and conversation history to give informed answers

RESPONSE FORMAT FOR PREDICTION QUESTIONS - CRITICAL:

**DO NOT INCLUDE:**
- Intro paragraphs about recent developments
- Current metrics section (price, returns, risk score, etc.)
- Recent news articles
- Any preliminary analysis

**START DIRECTLY WITH:**
"Looking ahead [X] years for [Company]..."

**THEN PROVIDE THREE SCENARIOS WITH SPECIFIC PRICE TARGETS:**

**Bull Case Scenario:**
- Specific price target: $X-Y (e.g., "$400-450 in 5 years")
- Probability: X%
- Supporting factors: [list 2-3 key reasons]

**Base Case Scenario:**
- Specific price target: $X-Y (e.g., "$350-400 in 5 years") 
- Probability: X% (usually 40-50%)
- Supporting factors: [list 2-3 key reasons]

**Bear Case Scenario:**
- Specific price target: $X-Y (e.g., "$250-300 in 5 years")
- Probability: X%
- Supporting factors: [list 2-3 key reasons]

**My [X]-Year Prediction:**
- Primary prediction: "$X-Y by [year]" (e.g., "$380-420 by 2029")
- Reasoning: [2-3 sentences explaining your primary prediction]
- Confidence level: [High/Medium/Low] confidence

**PRICE CALCULATION REQUIREMENTS:**
- Calculate from CURRENT PRICE shown in context (e.g., if current is $271)
- For 5-year predictions, typical growth ranges:
  - Bull case: 40-60% growth (e.g., $271 → $380-430)
  - Base case: 20-40% growth (e.g., $271 → $325-380)
  - Bear case: -10% to +10% (e.g., $271 → $245-300)
- For 10-year predictions, use 2x the 5-year growth rates
- Reference historical market averages (S&P 500 averages ~10% annually over long term)
- Adjust based on company-specific factors (tech stocks may grow faster, established companies slower)

**ABSOLUTELY FORBIDDEN:**
- Vague statements like "positive performance" or "could see growth"
- Statements without dollar amounts
- Generic "reasonable chance" language
- Any response that doesn't include specific price numbers

FORMATTING:
- Use **bold** for price targets
- Use bullet points for clarity
- Write naturally, not robotically

Remember: The user wants SPECIFIC PRICE PREDICTIONS. Always provide dollar amounts."""
            elif is_market_wide_question:
                system_prompt = """You are an expert financial advisor AI assistant for RiskLattice. The user is asking about the MARKET OVERALL or MULTIPLE STOCKS - provide a comprehensive analysis ranking stocks.

CRITICAL CONTEXT UNDERSTANDING RULES:
1. **Analyze ALL stocks in the watchlist data** - You have access to metrics for multiple stocks
2. **Rank stocks based on the question** - "most bullish" = highest returns + lowest risk, "best stocks" = best combination of metrics
3. **Provide a ranked list** - Top 5-10 stocks with detailed metrics for each
4. **Explain your ranking criteria** - Why each stock is bullish/bearish based on the data

RESPONSE FORMAT FOR MARKET-WIDE QUESTIONS:

**START WITH:**
A brief overview of what makes a stock "bullish" or "best" based on the current market data.

**THEN PROVIDE RANKED LIST (Top 5-10 stocks):**

For each stock in your ranked list, provide:
1. **Rank** (#1, #2, #3, etc.)
2. **Symbol** (e.g., AAPL)
3. **Key Metrics:**
   - Current Price: $X.XX
   - 7-Day Return: +X.XX%
   - Risk Score: XX/100 (lower is better)
   - Volatility: XX.XX%
4. **Why it's bullish/best:** 1-2 sentence explanation based on the metrics

**RANKING CRITERIA:**
- **Most Bullish Stocks:** Prioritize HIGH 7-day returns + LOW risk scores + LOW volatility
- **Best Stocks:** Balance of positive returns, low risk, stable volatility
- **Worst/Bearish Stocks:** Negative returns, high risk scores, high volatility

**END WITH:**
A summary statement about overall market trends based on the data.

FORMATTING:
- Use **bold** for stock symbols and key metrics
- Use numbered list for rankings
- Include all relevant metrics for transparency
- Write naturally and analytically"""
            else:
                system_prompt = """You are an expert financial advisor AI assistant for RiskLattice. You provide detailed, intelligent analysis about stocks, companies, and financial markets.

CRITICAL CONTEXT UNDERSTANDING RULES:
1. **ALWAYS check conversation history** - If the user asks follow-up questions without mentioning a stock name, you MUST look at previous messages to find which stock they're discussing
2. **NEVER give generic responses** - If asked about a specific stock or company, ALWAYS provide a detailed, substantive answer using available data
3. **Use ALL available context** - Check the watchlist data, news articles, and conversation history to give informed answers

RESPONSE STRUCTURE FOR STOCK QUESTIONS:

**FIRST: Human Conversational Opening (REQUIRED - 2-3 sentences)**
Write naturally, like talking to a friend. Example style:
- "Looking at Apple right now, I see some interesting developments..."
- "Apple's situation is pretty interesting - the company has been..."
- "From what I'm seeing with Apple, there are a few things worth noting..."

Then mention:
- Recent news or developments (from the news context if available)
- Past performance or historical context
- Your honest, straightforward assessment

**SECOND: Technical Analysis**
- Current Price: $X.XX
- 7-Day Return: +X.XX% or -X.XX%
- Risk Score: XX/100
- Volatility: XX.XX%
- Analysis of what these metrics mean

**THIRD: Recent News & Sources**
- List relevant news articles with full citations
- Format: "**Source:** [Publication] - [Title] ([URL])"
- Include dates when available

**FOURTH: Assessment & Outlook** (if applicable)
- Bullish factors
- Bearish factors
- Your honest take on direction

FOLLOW-UP QUESTION HANDLING:
- If user asks "give me a prediction" after asking about Apple, you MUST know they're asking about Apple
- Review conversation history to identify the stock being discussed
- NEVER say "I'm a financial AI assistant" - just answer the question directly

FORMATTING:
- Use **bold** for key metrics
- Use bullet points for clarity
- Always cite news sources with URLs
- Write naturally, not robotically

Remember: You have access to real stock data, news articles, and metrics. Use them to give detailed, intelligent answers. Be conversational but thorough."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history - CRITICAL for context understanding
            if conversation_history:
                # Add explicit instruction to use conversation context
                if len(conversation_history) > 0:
                    # Extract all mentioned stocks from conversation history
                    mentioned_stocks = []
                    for msg in conversation_history:
                        content = msg.get("content", str(msg)) if isinstance(msg, dict) else str(msg)
                        # Look for stock symbols and company names
                        import re
                        stock_pattern = r'\b(AAPL|TSLA|MSFT|GOOGL|AMZN|META|NVDA|NFLX|INTC|JPM|V|JNJ|WMT|PG|MA|HD|DIS|BAC|XOM|CVX|ABBV|PFE|COST|AVGO|PEP|TMO|ADBE|CSCO|CMCSA|COIN|NKE)\b'
                        company_pattern = r'\b(Apple|Tesla|Microsoft|Google|Amazon|Meta|Facebook|Nvidia|Netflix|Intel)\b'
                        if re.search(stock_pattern, content, re.IGNORECASE) or re.search(company_pattern, content, re.IGNORECASE):
                            mentioned_stocks.append(content[:100])  # Store snippet
                    
                    if mentioned_stocks:
                        messages.append({
                            "role": "system", 
                            "content": f"CONVERSATION CONTEXT: The user has been discussing these stocks/companies in previous messages: {', '.join(set(mentioned_stocks[:5]))}. If they ask follow-up questions without mentioning the stock name, refer back to these previous discussions."
                        })
                
                # Add actual conversation history
                for msg in conversation_history[-20:]:  # Keep last 20 messages
                    role = msg.get("role", "user") if isinstance(msg, dict) else "user"
                    content = msg.get("content", str(msg)) if isinstance(msg, dict) else str(msg)
                    messages.append({"role": role, "content": content})
            
            # Add current context
            if context_text:
                messages.append({"role": "system", "content": f"Additional context:{context_text}"})
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Detect question type to determine response length
            message_lower = user_message.lower()
            
            # Check conversation history for stock mentions if current message doesn't have one
            stock_mentioned_in_message = any(keyword in message_lower for keyword in [
                'stock', 'ticker', 'aapl', 'tsla', 'msft', 'googl', 'amzn', 'meta', 'nvda', 'nflx', 'intc',
                'apple', 'tesla', 'microsoft', 'google', 'amazon', 'facebook', 'nvidia', 'netflix', 'intel',
                'jpm', 'visa', 'walmart', 'costco', 'disney', 'coca', 'pepsi', 'nike'
            ])
            
            # Check conversation history
            stock_mentioned_in_history = False
            if conversation_history:
                for msg in conversation_history[-5:]:
                    content = (msg.get("content", "") if isinstance(msg, dict) else str(msg)).lower()
                    if any(kw in content for kw in ['apple', 'aapl', 'tesla', 'tsla', 'microsoft', 'msft', 'stock', 'ticker']):
                        stock_mentioned_in_history = True
                        break
            
            is_analytical_question = any(keyword in message_lower for keyword in [
                'why', 'predict', 'forecast', 'outlook', 'expect', 'projection', 'future', 'rise', 'fall', 
                'increase', 'decrease', 'year', 'years', 'long-term', 'short-term', 'opinion', 'think',
                'scenario', 'possibility', 'likely', 'chance', 'trend', 'direction', 'will it', 'looking like'
            ])
            
            is_stock_question = stock_mentioned_in_message or stock_mentioned_in_history or is_analytical_question
            
            # Give longer responses for prediction questions - these need detailed price targets
            # Use is_prediction_question we detected earlier
            if is_prediction_question:
                max_tokens = 2500  # Need more tokens for detailed price predictions
            elif is_market_wide_question:
                max_tokens = 2500  # Market-wide questions need space for multiple stock analyses
            elif is_analytical_question or is_stock_question:
                max_tokens = 2000  # Stock questions also need detailed responses
            else:
                max_tokens = 1000
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=max_tokens,
                    timeout=30  # 30 second timeout
                )
                
                result = response.choices[0].message.content.strip()
                if not result or len(result) < 10:
                    raise ValueError("Response too short or empty")
                return result
            except Exception as api_error:
                print(f"OpenAI API error: {api_error}, falling back to enhanced fallback")
                # Use enhanced fallback which can handle stock questions
                return self._chat_fallback(user_message, context_data, conversation_history)
        except Exception as e:
            print(f"LLM chat failed: {e}, falling back")
            # Always return a response, never fail
            return self._chat_fallback(user_message, context_data, conversation_history)
    
    def _chat_fallback(self, user_message: str, context_data: Optional[Dict] = None, conversation_history: Optional[List] = None) -> str:
        """Fallback response when OpenAI is not available - provides detailed responses."""
        import re
        message_lower = user_message.lower()
        
        # Detect stock symbols (common ones)
        stock_symbols_map = {
            'apple': 'AAPL', 'apples': 'AAPL', 'aapl': 'AAPL',
            'tesla': 'TSLA', 'tsla': 'TSLA',
            'microsoft': 'MSFT', 'msft': 'MSFT',
            'google': 'GOOGL', 'googl': 'GOOGL', 'alphabet': 'GOOGL',
            'amazon': 'AMZN', 'amzn': 'AMZN',
            'meta': 'META', 'facebook': 'META',
            'nvidia': 'NVDA', 'nvda': 'NVDA',
            'netflix': 'NFLX', 'nflx': 'NFLX',
            'intel': 'INTC', 'intc': 'INTC'
        }
        
        detected_symbol = None
        for keyword, symbol in stock_symbols_map.items():
            if keyword in message_lower:
                detected_symbol = symbol
                break
        
        # Check conversation history for stock context if not found in current message
        if not detected_symbol and conversation_history:
            # Check last 10 messages in reverse order (most recent first)
            for msg in reversed(conversation_history[-10:]):
                msg_content = (msg.get('content', '') if isinstance(msg, dict) else str(msg)).lower()
                # Check for company names and symbols
                for keyword, symbol in stock_symbols_map.items():
                    if keyword in msg_content or symbol.lower() in msg_content:
                        detected_symbol = symbol
                        break
                if detected_symbol:
                    break
                # Also check for ticker pattern
                ticker_pattern = r'\b([A-Z]{2,5})\b'
                import re
                matches = re.findall(ticker_pattern, msg_content if isinstance(msg, dict) else str(msg))
                if matches:
                    for match in matches:
                        if match.upper() in stock_symbols_map.values():
                            detected_symbol = match.upper()
                            break
                if detected_symbol:
                    break
        
        # Also try to find uppercase ticker symbols in the message
        if not detected_symbol:
            ticker_pattern = r'\b([A-Z]{2,5})\b'
            matches = re.findall(ticker_pattern, user_message)
            if matches:
                detected_symbol = matches[0].upper()
        
        # If still no symbol, check if it's a follow-up question about stocks
        is_followup_stock_question = any(word in message_lower for word in [
            'prediction', 'forecast', 'outlook', 'rise', 'fall', 'year', 'years',
            'think', 'opinion', 'believe', 'expect', 'future', 'going', 'will it',
            'looking like', 'what about', 'tell me about', 'how about', 'give me',
            'tell me', 'what do you think', 'do you think', 'will it'
        ])
        
        # If it's clearly a follow-up question but no stock detected, try to infer from context
        if is_followup_stock_question and not detected_symbol:
            # First try conversation history more thoroughly
            if conversation_history:
                # Look for any mention of stocks in recent messages
                for msg in reversed(conversation_history):
                    msg_content = (msg.get('content', '') if isinstance(msg, dict) else str(msg)).lower()
                    # Check for company names or tickers
                    for keyword, symbol in stock_symbols_map.items():
                        if keyword in msg_content or symbol.lower() in msg_content:
                            detected_symbol = symbol
                            break
                    if detected_symbol:
                        break
                    # Also check for ticker pattern
                    ticker_pattern = r'\b([A-Z]{2,5})\b'
                    matches = re.findall(ticker_pattern, msg_content if isinstance(msg, dict) else str(msg))
                    if matches:
                        detected_symbol = matches[0].upper()
                        break
            
            # If still no symbol and we have watchlist, use first stock as context
            if not detected_symbol and context_data and context_data.get('watchlist'):
                detected_symbol = context_data['watchlist'][0].get('symbol') if context_data['watchlist'] else None
        
        # Handle stock-specific questions - be more lenient with detection
        is_stock_question = (
            detected_symbol or 
            is_followup_stock_question or
            any(word in message_lower for word in ['stock', 'buy', 'sell', 'invest', 'future', 'risky', 'prediction', 'forecast', 'outlook', 'price', 'looking like', 'think', 'opinion', 'believe'])
        )
        
        if is_stock_question:
            response_parts = []
            
            # Get stock data from watchlist if available
            stock_data = None
            if context_data and context_data.get('watchlist'):
                for ticker in context_data['watchlist']:
                    if ticker.get('symbol') == detected_symbol or (detected_symbol and ticker.get('symbol', '').upper() == detected_symbol):
                        stock_data = ticker
                        break
            
            # Get news for this stock
            relevant_news = []
            if context_data and context_data.get('recent_news'):
                for article in context_data['recent_news']:
                    if detected_symbol and article.get('symbol', '').upper() == detected_symbol:
                        relevant_news.append(article)
                    elif not detected_symbol and ('stock' in message_lower or 'market' in message_lower):
                        relevant_news.append(article)
                relevant_news = relevant_news[:10]  # Limit to 10 articles
            
            # Build comprehensive response
            stock_name = detected_symbol if detected_symbol else "the stock"
            company_name_map = {
                'AAPL': 'Apple', 'TSLA': 'Tesla', 'MSFT': 'Microsoft', 'GOOGL': 'Google',
                'AMZN': 'Amazon', 'META': 'Meta', 'NVDA': 'Nvidia', 'NFLX': 'Netflix', 'INTC': 'Intel'
            }
            company_name = company_name_map.get(detected_symbol, detected_symbol) if detected_symbol else "this company"
            
            # START WITH CONVERSATIONAL PARAGRAPH
            conversational_intro = []
            
            if stock_data:
                price = stock_data.get('price', 0)
                risk_score = stock_data.get('risk_score', 0)
                return_7d = stock_data.get('return_7d', 0)
                volatility = stock_data.get('volatility', 0)
                
                # Build conversational intro based on news and performance
                conversational_intro.append(f"{company_name} announced some interesting developments recently, and honestly, I think it's worth paying attention to.")
                
                # Reference news if available
                if relevant_news:
                    first_news_title = relevant_news[0].get('title', '')
                    # Extract key phrases from news title
                    if first_news_title:
                        conversational_intro.append(f"Looking at the recent news, {first_news_title[:100]}...")
                
                # Mention past performance in human terms
                if return_7d > 2:
                    conversational_intro.append(f"In the past week, {company_name} has actually shown some decent momentum with prices climbing about {return_7d:.1f}%, which is pretty solid.")
                elif return_7d < -2:
                    conversational_intro.append(f"Looking back at the past week though, {company_name} has seen prices dip by about {abs(return_7d):.1f}%, which suggests there might be some concerns in the market.")
                else:
                    conversational_intro.append(f"Over the past week, {company_name} has been relatively stable, not showing huge swings either way.")
                
                # Give honest assessment
                if risk_score >= 70:
                    conversational_intro.append(f"Honestly, this feels like a higher-risk situation right now - the risk indicators are pretty elevated, so investors should really consider their tolerance for volatility.")
                elif risk_score >= 40:
                    conversational_intro.append(f"From what I'm seeing, this seems like a moderate-risk play - it's not the safest bet out there, but it's also not the most volatile either.")
                else:
                    conversational_intro.append(f"Honestly, the risk metrics look relatively reasonable here - it's not showing those red flags that would make me super concerned, though of course nothing's guaranteed in the market.")
            else:
                # If no data, still give conversational intro
                conversational_intro.append(f"{company_name} is definitely one of those stocks that people are always asking about.")
                if relevant_news:
                    conversational_intro.append(f"Looking at recent developments, there's been some interesting news coming out.")
                conversational_intro.append(f"From what I understand, historically this has been a company that's shown resilience, but market conditions can always shift.")
                conversational_intro.append(f"Honestly, without current metrics from your watchlist, I'd suggest adding it so we can get a clearer picture of what's happening right now.")
            
            # Add the conversational intro as the first part
            response_parts.append(" ".join(conversational_intro))
            response_parts.append("")  # Blank line before technical details
            
            # Now add technical section header
            response_parts.append(f"**Current Metrics & Analysis:**")
            
            if stock_data:
                
                response_parts.append(f"- **Current Price:** ${price:.2f}")
                response_parts.append(f"- **7-Day Return:** {return_7d:+.2f}%")
                response_parts.append(f"- **Risk Score:** {risk_score:.1f}/100")
                response_parts.append(f"- **Volatility:** {volatility:.1f}%")
                
                # Risk assessment
                if risk_score >= 70:
                    risk_level = "HIGH RISK"
                    risk_advice = "The stock currently shows high risk levels. Consider this carefully before investing and ensure it aligns with your risk tolerance."
                elif risk_score >= 40:
                    risk_level = "MODERATE RISK"
                    risk_advice = "The stock shows moderate risk. This may be suitable for investors with balanced portfolios."
                else:
                    risk_level = "LOW RISK"
                    risk_advice = "The stock shows relatively low risk levels, though all investments carry inherent risk."
                
                response_parts.append(f"\n**Risk Assessment:** {risk_level}")
                response_parts.append(risk_advice)
            else:
                response_parts.append(f"\n**Note:** {stock_name} is not currently in your watchlist. To get detailed metrics, add it to your watchlist using the Dashboard.")
                response_parts.append(f"\n**General Risk Considerations:**")
                response_parts.append("- All stock investments carry inherent risk. Consider your investment goals and risk tolerance.")
                response_parts.append("- Research the company's fundamentals, financial health, and market position.")
                response_parts.append("- Monitor market trends and news that could impact the stock.")
                response_parts.append("- Diversify your portfolio to manage overall risk.")
            
            # Add news sources
            if relevant_news:
                response_parts.append(f"\n**Recent News & Sources:**")
                for article in relevant_news[:5]:  # Show top 5
                    title = article.get('title', '')
                    source = article.get('source', 'Unknown Source')
                    url = article.get('url', '')
                    symbol = article.get('symbol', '')
                    if url:
                        response_parts.append(f"- [{symbol}] {title} (Source: {source} - {url})")
                    else:
                        response_parts.append(f"- [{symbol}] {title} (Source: {source})")
            
            # Handle price movement questions
            if any(word in message_lower for word in ['rise', 'fall', 'increase', 'decrease', 'go up', 'go down', 'price prediction']):
                response_parts.append(f"\n**Price Movement Analysis:**")
                if stock_data:
                    risk_score = stock_data.get('risk_score', 0)
                    return_7d = stock_data.get('return_7d', 0)
                    volatility = stock_data.get('volatility', 0)
                    
                    # Bullish factors
                    bullish_factors = []
                    if return_7d > 0:
                        bullish_factors.append(f"Recent positive momentum with {return_7d:+.2f}% gains")
                    if risk_score < 50:
                        bullish_factors.append(f"Relatively low risk score of {risk_score:.1f}")
                    if volatility < 30:
                        bullish_factors.append(f"Moderate volatility suggesting stability")
                    
                    # Bearish factors
                    bearish_factors = []
                    if return_7d < 0:
                        bearish_factors.append(f"Recent decline of {abs(return_7d):.2f}%")
                    if risk_score > 60:
                        bearish_factors.append(f"Elevated risk score of {risk_score:.1f}")
                    if volatility > 40:
                        bearish_factors.append(f"High volatility of {volatility:.1f}% indicating uncertainty")
                    
                    if bullish_factors:
                        response_parts.append(f"\n**Factors that could push price up:**")
                        for factor in bullish_factors:
                            response_parts.append(f"- {factor}")
                    
                    if bearish_factors:
                        response_parts.append(f"\n**Factors that could push price down:**")
                        for factor in bearish_factors:
                            response_parts.append(f"- {factor}")
                    
                    # Give opinion
                    if return_7d > 2 and risk_score < 50:
                        response_parts.append(f"\n**My take:** Given the positive momentum and relatively low risk, I think there's potential for continued upward movement in the short term. However, keep an eye on market conditions and any breaking news that could change the trend.")
                    elif return_7d < -2 or risk_score > 60:
                        response_parts.append(f"\n**My take:** The recent negative pressure and elevated risk suggest there might be downward pressure in the near term. I'd be cautious and watch for signs of stabilization before making significant moves.")
                    else:
                        response_parts.append(f"\n**My take:** The mixed signals suggest we could see movement in either direction. The volatility of {volatility:.1f}% means we should expect some swings, so it's really a question of timing and risk tolerance.")
            
            # Handle long-term prediction questions
            if any(word in message_lower for word in ['year', 'years', 'long-term', '5 year', '10 year', '5-year', '10-year', 'decade']):
                years_match = re.search(r'(\d+)\s*(?:year|yr)', message_lower)
                years = int(years_match.group(1)) if years_match else 5
                
                response_parts.append(f"\n**{years}-Year Outlook:**")
                response_parts.append(f"\nLooking ahead {years} years is always tricky, but let me give you my honest take.")
                
                if stock_data:
                    risk_score = stock_data.get('risk_score', 0)
                    
                    response_parts.append(f"\n**Bull Case Scenario:**")
                    response_parts.append(f"- If {company_name} can maintain its competitive position and adapt to market changes")
                    response_parts.append(f"- Continued innovation and market expansion could drive growth")
                    response_parts.append(f"- Technology sector trends could favor established players like {company_name}")
                    
                    response_parts.append(f"\n**Base Case Scenario:**")
                    response_parts.append(f"- Steady growth with normal market cycles and volatility")
                    response_parts.append(f"- Some ups and downs but overall positive trajectory if fundamentals remain strong")
                    response_parts.append(f"- Current risk metrics suggest reasonable foundation for growth")
                    
                    response_parts.append(f"\n**Bear Case Scenario:**")
                    response_parts.append(f"- Market disruptions, regulatory changes, or competitive pressure could create headwinds")
                    response_parts.append(f"- Technology shifts could disrupt the business model")
                    response_parts.append(f"- Economic downturns could impact performance")
                    
                    response_parts.append(f"\n**My {years}-year prediction:** Honestly, predicting {years} years out is speculative, but based on current metrics, I think {company_name} has a reasonable chance of positive performance if they execute well. The relatively {'low' if risk_score < 50 else 'moderate' if risk_score < 70 else 'high'} risk score of {risk_score:.1f} suggests a {'stable' if risk_score < 50 else 'moderate' if risk_score < 70 else 'volatile'} foundation. However, so much can change in {years} years - new competitors, market shifts, technological disruptions. I'd say the probability is decent for positive returns, but with significant uncertainty.")
                else:
                    response_parts.append(f"\nTo give you a more detailed {years}-year outlook, I'd need current metrics. Add {stock_name} to your watchlist to get ongoing analysis and better predictions.")
            
            # Handle "why" questions
            if 'why' in message_lower:
                if stock_data:
                    risk_score = stock_data.get('risk_score', 0)
                    return_7d = stock_data.get('return_7d', 0)
                    volatility = stock_data.get('volatility', 0)
                    
                    response_parts.append(f"\n**Reasoning Behind My Assessment:**")
                    response_parts.append(f"\nHere's why I think what I do:")
                    response_parts.append(f"- Current risk score of {risk_score:.1f} suggests {'lower' if risk_score < 50 else 'moderate' if risk_score < 70 else 'higher'} risk levels")
                    response_parts.append(f"- 7-day return of {return_7d:+.2f}% shows {'positive' if return_7d > 0 else 'negative'} recent momentum")
                    response_parts.append(f"- Volatility of {volatility:.1f}% indicates {'more stable' if volatility < 30 else 'moderate' if volatility < 50 else 'more volatile'} price movements")
                    
                    if relevant_news:
                        response_parts.append(f"- Recent news developments suggest market sentiment is {'positive' if len([n for n in relevant_news if any(word in n.get('title', '').lower() for word in ['growth', 'gain', 'up', 'surge', 'rise'])]) > len([n for n in relevant_news if any(word in n.get('title', '').lower() for word in ['decline', 'drop', 'fall', 'loss', 'down'])]) else 'mixed'}")
                    
                    response_parts.append(f"\nThese factors combined lead me to my current assessment.")
            
            # Future outlook (general)
            if ('future' in message_lower or 'predict' in message_lower or 'outlook' in message_lower) and 'year' not in message_lower:
                response_parts.append(f"\n**Future Outlook:**")
                if stock_data:
                    if stock_data.get('risk_score', 0) > 60:
                        response_parts.append(f"Current risk indicators suggest elevated volatility may continue. Monitor closely for any significant news or market changes.")
                    else:
                        response_parts.append(f"Current metrics suggest relatively stable conditions, though market conditions can change rapidly. Continue monitoring key indicators.")
                else:
                    response_parts.append(f"To provide a detailed outlook, add {stock_name} to your watchlist for ongoing risk analysis and predictions.")
            
            response_parts.append(f"\n**Disclaimer:** This analysis is for informational purposes only and does not constitute financial advice. Always conduct your own research and consult with a financial advisor before making investment decisions.")
            
            return "\n".join(response_parts)
        
        # General financial concepts
        if any(word in message_lower for word in ['risk', 'risk score']):
            return "Risk scores range from 0-100, where higher scores indicate greater risk. They combine market volatility, price movements, and news sentiment. A score above 70 is considered high risk, 40-70 is moderate, and below 40 is low risk."
        
        if any(word in message_lower for word in ['volatility', 'volatile']):
            return "Volatility measures how much a stock's price fluctuates. Higher volatility means larger price swings and typically higher risk. It's calculated as the annualized standard deviation of returns."
        
        if any(word in message_lower for word in ['drawdown', 'max drawdown']):
            return "Max drawdown is the largest peak-to-trough decline in price over a period. It shows the worst-case scenario loss from a peak value, which is important for risk assessment."
        
        if any(word in message_lower for word in ['watchlist']):
            if context_data and context_data.get('watchlist'):
                watchlist = context_data['watchlist']
                symbols = [t.get('symbol', '') for t in watchlist[:5]]
                return f"Your watchlist includes: {', '.join(symbols)}. Use the dashboard to view detailed risk analysis for each stock."
            return "You can add stocks to your watchlist using the ticker symbol (e.g., AAPL, TSLA). The platform will track their risk scores, volatility, and market performance."
        
        # If it seems like a stock question but we couldn't identify the stock
        if is_followup_stock_question:
            return f"I'd be happy to give you a prediction or analysis! Could you clarify which stock you're asking about? For example, 'What's your 5-year prediction for Apple?' or 'Do you think Tesla will rise or fall?'"
        
        # Default response
        return "I'm a financial AI assistant. I can help explain risk scores, volatility, market trends, and answer questions about stocks in your watchlist. Ask me about any financial concept or stock analysis!"

