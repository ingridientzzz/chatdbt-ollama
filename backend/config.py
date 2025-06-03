import os
from dotenv import load_dotenv

class Config:

    load_dotenv()
    # Ollama configuration
    OLLAMA_HOST = os.getenv("OLLAMA_HOST")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL")

    # DBT project configuration
    DBT_PROJECT_PATH = os.getenv("DBT_PROJECT_PATH")
    DBT_DOCS_PATH = os.getenv("DBT_DOCS_PATH")

    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Index storage
    INDEX_STORAGE_PATH = os.getenv("INDEX_STORAGE_PATH", "./storage")
