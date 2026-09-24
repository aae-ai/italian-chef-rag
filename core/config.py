"""
Config - ChefBot Configuration
==============================

Required Environment Variables:
- GROQ_API_KEY: API key for Groq LLM
- MONGO_URI: MongoDB connection string
- PINECONE_API_KEY: Pinecone vector DB API key
- REDIS_URL: Redis connection string (NEW)

Optional:
- LLM_MODEL: Model name (default: llama-3.1-70b-versatile)
- EMBEDDING_MODEL: Embedding model (default: embed-english-v3.0)
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # =================================================================
    # LLM Configuration
    # =================================================================
    LLM_MODEL = "openai/gpt-oss-120b"

    # =================================================================
    # Groq API
    # =================================================================
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is required")

    # =================================================================
    # MongoDB Configuration
    # =================================================================
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable is required")

    MONGO_DB_NAME = "chef_bot"
    MONGO_COLLECTION_NAME ="chat_history"

    # =================================================================
    # Pinecone Configuration
    # =================================================================
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable is required")

   # Pinecone
    INDEX_NAME = "italian-recipes"
    CLOUD =  "aws"
    REGION = "us-east-1"
    NAMESPACE = "example-namespace"
    EMBEDDING_MODEL = "llama-text-embed-v2"  
    # =================================================================
    # Redis Configuration (NEW)
    # =================================================================
    REDIS_URL = os.getenv("REDIS_URL")
    if not REDIS_URL:
        # Default to local Redis for development
        REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        print("⚠️ WARNING: Using default Redis URL. Set REDIS_URL for production!")

    # =================================================================
    # Cache Configuration
    # =================================================================
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

    # =================================================================
    # Rate Limiting Configuration
    # =================================================================
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # =================================================================
    # Data Path
    # =================================================================
    JSON_DATA_PATH = os.getenv("JSON_DATA_PATH", "data/recipes.json")