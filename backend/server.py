from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from openai import OpenAI
from duckduckgo_search import DDGS
import asyncio
from concurrent.futures import ThreadPoolExecutor
from news_api import news_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Create the main app without a prefix
app = FastAPI(title="FinanceSpace API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=5)

# Define Models
class QueryRequest(BaseModel):
    query: str
    type: str = "general"  # "general", "search", "combined"

class QueryResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    response: str
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class SearchResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    results: List[SearchResult]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CombinedResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    search_results: List[SearchResult]
    ai_summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    query: str
    response: str
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# AI Research Agent Functions
async def get_gpt_response(query: str, context: str = "") -> str:
    """Get response from OpenAI GPT"""
    try:
        def call_openai():
            messages = [
                {"role": "system", "content": "You are a helpful research assistant specializing in finance and space research. Provide accurate, informative responses."}
            ]
            if context:
                messages.append({"role": "system", "content": f"Context: {context}"})
            messages.append({"role": "user", "content": query})
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, call_openai)
        return response
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

async def search_duckduckgo(query: str, max_results: int = 5) -> List[SearchResult]:
    """Search DuckDuckGo and return results"""
    try:
        def search():
            with DDGS() as ddgs:
                results = []
                for result in ddgs.text(query, max_results=max_results):
                    results.append(SearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', '')
                    ))
                return results
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(executor, search)
        return results
    except Exception as e:
        logging.error(f"DuckDuckGo search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search service error: {str(e)}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "FinanceSpace API - Ready to research!"}

@api_router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a general AI query"""
    try:
        response = await get_gpt_response(request.query)
        
        # Store in conversation history
        conversation = ConversationHistory(
            query=request.query,
            response=response,
            type="general"
        )
        await db.conversations.insert_one(conversation.dict())
        
        return QueryResponse(
            query=request.query,
            response=response,
            type="general"
        )
    except Exception as e:
        logging.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/search", response_model=SearchResponse)
async def process_search(request: QueryRequest):
    """Process a search query"""
    try:
        results = await search_duckduckgo(request.query)
        
        # Store in conversation history
        conversation = ConversationHistory(
            query=request.query,
            response=f"Found {len(results)} search results",
            type="search"
        )
        await db.conversations.insert_one(conversation.dict())
        
        return SearchResponse(
            query=request.query,
            results=results
        )
    except Exception as e:
        logging.error(f"Search processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/combined", response_model=CombinedResponse)
async def process_combined(request: QueryRequest):
    """Process a combined search + AI analysis"""
    try:
        # Get search results
        search_results = await search_duckduckgo(request.query)
        
        # Create context from search results
        context = "Search results:\n"
        for i, result in enumerate(search_results[:3], 1):
            context += f"{i}. {result.title}\n{result.snippet}\n\n"
        
        # Get AI summary
        ai_summary = await get_gpt_response(
            f"Based on the search results, provide a comprehensive summary about: {request.query}",
            context
        )
        
        # Store in conversation history
        conversation = ConversationHistory(
            query=request.query,
            response=ai_summary,
            type="combined"
        )
        await db.conversations.insert_one(conversation.dict())
        
        return CombinedResponse(
            query=request.query,
            search_results=search_results,
            ai_summary=ai_summary
        )
    except Exception as e:
        logging.error(f"Combined processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history", response_model=List[ConversationHistory])
async def get_conversation_history(limit: int = 10):
    """Get conversation history"""
    try:
        conversations = await db.conversations.find().sort("timestamp", -1).limit(limit).to_list(limit)
        return [ConversationHistory(**conv) for conv in conversations]
    except Exception as e:
        logging.error(f"History retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

# Include the news router under the API router
api_router.include_router(news_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    executor.shutdown(wait=False)