import os
from dotenv import load_dotenv

class Config:

    load_dotenv()
    # Ollama configuration - get env variables or use defaults
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    # DBT project configuration
    DBT_PROJECT_PATH = os.getenv("DBT_PROJECT_PATH")

    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Index storage
    INDEX_STORAGE_PATH = os.getenv("INDEX_STORAGE_PATH", "./storage")
