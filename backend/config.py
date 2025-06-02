import os
from pathlib import Path

class Config:
    # Ollama configuration
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    
    # DBT project configuration
    DBT_PROJECT_PATH='/Users/marquein/adsk_git_repos/adp-astro-eda/dags/dbt/access/assignment'
    # DBT_PROJECT_PATH = os.getenv("DBT_PROJECT_PATH", "./dbt_project")
    DBT_DOCS_PATH = os.getenv("DBT_DOCS_PATH", "./dbt_project/target/compiled")
    
    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Index storage
    INDEX_STORAGE_PATH = os.getenv("INDEX_STORAGE_PATH", "./storage")