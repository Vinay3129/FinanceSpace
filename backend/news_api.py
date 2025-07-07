import requests
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import logging
import os
from concurrent.futures import ThreadPoolExecutor

# News API keys
NEWSDATA_API_KEY = "pub_f1b94a0af239455b9d6b8c8197720de0"
GNEWS_API_KEY = "c22aa4e5b3154001c857762ecd73d7ff"
MEDIASTACK_API_KEY = "4e4537e9a8cbcde4a88979ed2ffc691f"
FINNHUB_API_KEY = "d12jnq1r01qmhi3j2sogd12jnq1r01qmhi3j2sp0"

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=5)

# Models
class NewsArticle(BaseModel):
    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class NewsResponse(BaseModel):
    id: str = uuid.uuid4().hex
    category: str
    region: Optional[str] = None
    articles: List[NewsArticle]
    timestamp: datetime = datetime.utcnow()

# Create a router
news_router = APIRouter(prefix="/news")

@news_router.get("/", response_model=NewsResponse)
async def get_news(category: str = "business", region: str = None):
    """
    Get news articles by category and region
    Categories: business, technology, science, health, entertainment, sports, cryptocurrency
    Regions: us, in, eu, asia, global
    """
    try:
        # Try primary source first (NewsData.io)
        articles = await fetch_from_newsdata(category, region)
        
        # If primary source fails or returns no results, try fallbacks
        if not articles:
            if category.lower() == "cryptocurrency" or category.lower() == "crypto":
                # Try crypto-specific fallbacks
                articles = await fetch_crypto_news()
            else:
                # Try general fallbacks
                articles = await fetch_fallback_news(category, region)
        
        return NewsResponse(
            category=category,
            region=region,
            articles=articles
        )
    except Exception as e:
        logging.error(f"News API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")

async def fetch_from_newsdata(category, region=None):
    """Fetch news from NewsData.io API"""
    def _fetch():
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&language=en"
        
        # Map region to country codes
        if region:
            if region == "us":
                url += "&country=us"
            elif region == "in":
                url += "&country=in"
            elif region == "eu":
                url += "&country=de,fr,it,gb,es,nl"
            elif region == "asia":
                url += "&country=cn,jp,in,id,sg,my,th,vn,kr"
        
        # Map category
        if category:
            if category.lower() == "crypto" or category.lower() == "cryptocurrency":
                url += "&category=cryptocurrency"
            else:
                url += f"&category={category.lower()}"
        
        response = requests.get(url)
        data = response.json()
        
        if not data.get("results"):
            return []
        
        articles = []
        for item in data["results"]:
            articles.append(NewsArticle(
                title=item.get("title", ""),
                url=item.get("link", ""),
                source=item.get("source_id", "NewsData.io"),
                published_at=item.get("pubDate"),
                description=item.get("description", ""),
                image_url=item.get("image_url")
            ))
        
        return articles
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _fetch)

async def fetch_crypto_news():
    """Fetch cryptocurrency news from multiple sources with fallback"""
    sources = [
        fetch_crypto_from_newsdata,
        fetch_crypto_from_gnews,
        fetch_crypto_from_finnhub
    ]
    
    for source_func in sources:
        try:
            articles = await source_func()
            if articles and len(articles) > 0:
                return articles
        except Exception as e:
            logging.warning(f"Crypto news source failed: {str(e)}")
    
    return []  # All sources failed

async def fetch_crypto_from_newsdata():
    """Fetch crypto news from NewsData.io"""
    def _fetch():
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&language=en&category=cryptocurrency"
        response = requests.get(url)
        data = response.json()
        
        if not data.get("results"):
            return []
        
        articles = []
        for item in data["results"]:
            articles.append(NewsArticle(
                title=item.get("title", ""),
                url=item.get("link", ""),
                source=item.get("source_id", "NewsData.io"),
                published_at=item.get("pubDate"),
                description=item.get("description", ""),
                image_url=item.get("image_url")
            ))
        
        return articles
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _fetch)

async def fetch_crypto_from_gnews():
    """Fetch crypto news from GNews"""
    def _fetch():
        url = f"https://gnews.io/api/v4/search?q=crypto&token={GNEWS_API_KEY}&lang=en"
        response = requests.get(url)
        data = response.json()
        
        if not data.get("articles"):
            return []
        
        articles = []
        for item in data["articles"]:
            articles.append(NewsArticle(
                title=item.get("title", ""),
                url=item.get("url", ""),
                source=item.get("source", {}).get("name", "GNews"),
                published_at=item.get("publishedAt"),
                description=item.get("description", ""),
                image_url=item.get("image")
            ))
        
        return articles
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _fetch)

async def fetch_crypto_from_finnhub():
    """Fetch crypto news from Finnhub"""
    def _fetch():
        url = f"https://finnhub.io/api/v1/news?category=crypto&token={FINNHUB_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if not data:
            return []
        
        articles = []
        for item in data:
            articles.append(NewsArticle(
                title=item.get("headline", ""),
                url=item.get("url", ""),
                source=item.get("source", "Finnhub"),
                published_at=item.get("datetime"),
                description=item.get("summary", ""),
                image_url=item.get("image")
            ))
        
        return articles
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _fetch)

async def fetch_fallback_news(category, region=None):
    """Fetch news from fallback sources"""
    # Implement additional fallback sources if needed
    return []