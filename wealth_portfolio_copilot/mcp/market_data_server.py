"""MCP Server for Market Data - Fetches live stock prices and SEC filings."""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import yfinance as yf
from sec_edgar_downloader import Downloader

from config.settings import settings


class MarketDataServer:
    """
    MCP Server for fetching market data.
    Provides live stock prices, company information, and SEC filings.
    """
    
    def __init__(self):
        """Initialize the market data server."""
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.sec_downloader = Downloader(settings.SEC_EDGAR_EMAIL)
    
    async def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """
        Get current stock price and basic metrics.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            Dictionary with price and metrics
        """
        # Check cache
        cache_key = f"price_{ticker}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return cached_data
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            data = {
                "ticker": ticker,
                "current_price": info.get('currentPrice', info.get('regularMarketPrice')),
                "currency": info.get('currency', 'USD'),
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "dividend_yield": info.get('dividendYield'),
                "52_week_high": info.get('fiftyTwoWeekHigh'),
                "52_week_low": info.get('fiftyTwoWeekLow'),
                "volume": info.get('volume'),
                "avg_volume": info.get('averageVolume'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = (data, datetime.now())
            
            return data
            
        except Exception as e:
            return {
                "error": str(e),
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_stock_history(self, ticker: str, period: str = "1mo") -> Dict[str, Any]:
        """
        Get historical stock price data.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            Dictionary with historical price data
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            data = {
                "ticker": ticker,
                "period": period,
                "history": [
                    {
                        "date": idx.strftime('%Y-%m-%d'),
                        "open": row['Open'],
                        "high": row['High'],
                        "low": row['Low'],
                        "close": row['Close'],
                        "volume": row['Volume']
                    }
                    for idx, row in hist.iterrows()
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            return {
                "error": str(e),
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get detailed company information.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with company information
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            data = {
                "ticker": ticker,
                "company_name": info.get('longName'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "description": info.get('longBusinessSummary'),
                "website": info.get('website'),
                "headquarters": info.get('city'),
                "employees": info.get('fullTimeEmployees'),
                "ceo": info.get('companyOfficers', [{}])[0].get('name') if info.get('companyOfficers') else None,
                "timestamp": datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            return {
                "error": str(e),
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_sec_filings(self, ticker: str, form_type: str = "10-K", limit: int = 5) -> Dict[str, Any]:
        """
        Get SEC filings for a company.
        
        Args:
            ticker: Stock ticker symbol
            form_type: Type of form ('10-K', '10-Q', '8-K', etc.)
            limit: Maximum number of filings to return
            
        Returns:
            Dictionary with SEC filing information
        """
        try:
            # Download SEC filings
            self.sec_downloader.get_after_date(form_type, ticker, limit=limit)
            
            # Note: In production, you'd parse the actual filings
            # This is a simplified version
            data = {
                "ticker": ticker,
                "form_type": form_type,
                "filings": [
                    {
                        "form": form_type,
                        "filing_date": datetime.now().strftime('%Y-%m-%d'),
                        "accession_number": f"EXAMPLE-{datetime.now().strftime('%Y%m%d')}-{i}",
                        "description": f"{form_type} filing for {ticker}"
                    }
                    for i in range(limit)
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            return {
                "error": str(e),
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_market_news(self, ticker: str) -> Dict[str, Any]:
        """
        Get recent news about a stock.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with news articles
        """
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            data = {
                "ticker": ticker,
                "news": [
                    {
                        "title": article.get('title'),
                        "publisher": article.get('publisher'),
                        "link": article.get('link'),
                        "published_at": datetime.fromtimestamp(article.get('providerPublishTime')).isoformat() if article.get('providerPublishTime') else None
                    }
                    for article in news[:5]  # Top 5 news items
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            return {
                "error": str(e),
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for stocks by company name or ticker.
        
        Args:
            query: Search query
            
        Returns:
            List of matching stocks
        """
        # This is a simplified implementation
        # In production, you'd use a proper search API
        try:
            # Try as ticker first
            stock = yf.Ticker(query.upper())
            info = stock.info
            
            if info and info.get('shortName'):
                return [{
                    "ticker": query.upper(),
                    "name": info.get('shortName'),
                    "sector": info.get('sector'),
                    "match_score": 1.0
                }]
            
            return []
            
        except Exception:
            return []


# Singleton instance
market_data_server = MarketDataServer()
