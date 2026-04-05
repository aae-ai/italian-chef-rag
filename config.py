import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    INDEX_NAME = "italian-recipes"
    NAMESPACE = "example-namespace"
    CLOUD = "aws"
    REGION = "us-east-1"
    
    EMBEDDING_MODEL = "llama-text-embed-v2"
    LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    JSON_DATA_PATH = os.path.join(BASE_DIR, "italian_pinecone.json")
    HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
