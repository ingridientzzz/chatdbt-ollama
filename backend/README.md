# ChatDBT Backend with Ollama

This is the backend service for ChatDBT that uses Ollama for local LLM inference.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt

2. **Install and setup Ollama:**

    # Pull required models
    ```bash
    ollama pull llama2          # or mistral, codellama, etc.
    ollama pull nomic-embed-text  # for embeddings
    ```

3. **Set environment variables:**
    ```bash
    export DBT_PROJECT_PATH="/path/to/your/dbt/project"
    export OLLAMA_MODEL="llama2"  # or your preferred model
    export OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
    ```


4. **Run the server:**
    ```bash
    python main.py
    ```

    or with uvicorn:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

**Configuration**
All configuration is handled through environment variables:

- `DBT_PROJECT_PATH`: Path to your dbt project (required)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model to use (default: llama2)
- `OLLAMA_EMBEDDING_MODEL`: Embedding model (default: nomic-embed-text)
- `INDEX_STORAGE_PATH`: Where to store the vector index (default: ./storage)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

**API Endpoints**

- `GET /`: Health check
- `GET /health`: Detailed health status
- `POST /chat`: Chat with your dbt project
- `POST /refresh-index`: Refresh the index with latest dbt files

**Troubleshooting**

1. Ollama connection issues:
    - Ensure Ollama is running: `ollama serve`
    - Check if models are installed: `ollama list`

2. No documents found:
    Verify `DBT_PROJECT_PATH` points to a valid dbt project
    Ensure the project has models in the `models/` directory

3. Memory issues:
    - Try smaller models like `llama2:7b` instead of larger ones
    - Reduce `chunk_size` in the configuration