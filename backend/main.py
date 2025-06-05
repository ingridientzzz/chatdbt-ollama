import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings

from config import Config
from dbt_loader import DBTProjectLoader

app = FastAPI(title="ChatDBT with Ollama")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration
config = Config()

# Global variables
chat_engine = None
index = None

class ChatMessage(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None

def initialize_llama_index():
    """Initialize LlamaIndex with Ollama"""
    global chat_engine, index
    
    try:
        # Configure Ollama LLM
        llm = Ollama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_HOST,
            temperature=0.1,
            request_timeout=120.0
        )
        
        # Configure Ollama embeddings
        embed_model = OllamaEmbedding(
            model_name=config.OLLAMA_EMBEDDING_MODEL,
            base_url=config.OLLAMA_HOST
        )
        
        # Set global settings
        Settings.llm = llm
        Settings.embed_model = embed_model
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 20
        
        # Try to load existing index
        storage_path = Path(config.INDEX_STORAGE_PATH)
        
        if storage_path.exists() and (storage_path / "index_store.json").exists():
            print("Loading existing index...")
            storage_context = StorageContext.from_defaults(persist_dir=str(storage_path))
            index = load_index_from_storage(storage_context)
        else:
            print("Creating new index from DBT project...")
            # Load DBT project
            loader = DBTProjectLoader(config.DBT_PROJECT_PATH)
            documents = loader.load_dbt_files()
            
            if not documents:
                raise Exception("No DBT documents found. Please check your DBT_PROJECT_PATH.")
            
            print(f"Loaded {len(documents)} documents from DBT project")
            
            # Create index
            index = VectorStoreIndex.from_documents(documents)
            
            # Persist index
            storage_path.mkdir(exist_ok=True)
            index.storage_context.persist(persist_dir=str(storage_path))
        
        # Create chat engine
        chat_engine = CondensePlusContextChatEngine.from_defaults(
            index.as_retriever(similarity_top_k=5),
            system_message=(
                "You are a helpful assistant specialized in dbt (data build tool) projects. "
                "You can help users understand their data models, transformations, and documentation. "
                "When answering questions, provide specific information about the dbt models, "
                "their relationships, and how they transform data. "
                "If you reference specific files or models, mention their names clearly."
            )
        )
        
        print("LlamaIndex initialized successfully.")
        
    except Exception as e:
        print(f"Error initializing LlamaIndex: {e}")
        raise e

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    initialize_llama_index()

@app.get("/")
async def root():
    return {"message": "ChatDBT with Ollama API is running."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Ollama connection
        llm = Ollama(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST)
        test_response = llm.complete("Hello")
        
        return {
            "status": "healthy",
            "ollama_model": config.OLLAMA_MODEL,
            "ollama_host": config.OLLAMA_HOST,
            "index_loaded": index is not None,
            "chat_engine_ready": chat_engine is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat endpoint"""
    if not chat_engine:
        raise HTTPException(status_code=500, detail="Chat engine not initialized")
    
    try:
        # Get response from chat engine
        response = chat_engine.chat(message.message)
        
        # Extract sources if available
        sources = []
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                if hasattr(node, 'metadata') and 'file_path' in node.metadata:
                    sources.append(node.metadata['file_path'])
        
        return ChatResponse(
            response=str(response),
            sources=sources[:5]  # Limit to top 5 sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/refresh-index")
async def refresh_index():
    """Refresh the index by reloading DBT project"""
    try:
        global index, chat_engine
        
        # Reload DBT project
        loader = DBTProjectLoader(config.DBT_PROJECT_PATH)
        documents = loader.load_dbt_files()
        
        if not documents:
            raise HTTPException(status_code=400, detail="No DBT documents found")
        
        # Recreate index
        index = VectorStoreIndex.from_documents(documents)
        
        # Persist updated index
        storage_path = Path(config.INDEX_STORAGE_PATH)
        storage_path.mkdir(exist_ok=True)
        index.storage_context.persist(persist_dir=str(storage_path))
        
        # Recreate chat engine
        chat_engine = CondensePlusContextChatEngine.from_defaults(
            index.as_retriever(similarity_top_k=5),
            system_message=(
                "You are a helpful assistant specialized in dbt (data build tool) projects. "
                "You can help users understand their data models, transformations, and documentation. "
                "When answering questions, provide specific information about the dbt models, "
                "their relationships, and how they transform data. "
                "If you reference specific files or models, mention their names clearly."
            )
        )
        
        return {"message": f"Index refreshed successfully with {len(documents)} documents"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing index: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)