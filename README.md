# ChatDBT Backend with Ollama

This is the backend service for ChatDBT that uses Ollama for local LLM inference.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install and setup Ollama:**

    Install ollama from [ollama.com](https://ollama.com/)

    Start ollama server:
    ```bash
    ollama serve
    ```

    In other CLI prompt, pull the required models
    ```bash
    ollama pull qwen3:4b          # or mistral, codellama, etc.
    ollama pull nomic-embed-text  # for embeddings
    ```

    Note: Thinking models like `qwen3:4b` are good since they include trail of thought and we can see how they arrived at that answer to prompt

3. **Set environment variables:**
    Create `.env` file in `/backend` by copying `.env.example`

    ```ini
    DBT_PROJECT_PATH=path/to/your/dbt/project

    OLLAMA_HOST=http://localhost:11434
    OLLAMA_MODEL=qwen3:4b
    OLLAMA_EMBEDDING_MODEL=nomic-embed-text

    HOST=0.0.0.0
    PORT=8000
    ```


4. **Run the backend server:**
    ```bash
    cd backend
    python main.py
    ```

    or with uvicorn:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    Backend is running if you see this output:
    ```bash
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
    ```

5. **Run the frontend server:**
    On first run:
    ```bash
    cd frontend
    npm install && npm run dev
    ```

    Or, for consecutive runs, simply run the server itself:
    ```bash
    npm run dev
    ```

    Frontend is running if you see output:
    ```bash
        - Local:        http://localhost:3000
        - Environments: .env.local
    ```

    Open [http://localhost:3000](http://localhost:3000)

    Tip: 
    If you encounter: `Cannot connect to backend. Make sure Ollama is running and the backend server is started.`, then just refresh or reload the tab if it says not connected.

    Click on `Refresh` to recreate Vector store


**Configuration**
All configuration is handled through environment variables:

- `DBT_PROJECT_PATH`: Path to your dbt project (required)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model to use (default: qwen3:4b)
- `OLLAMA_EMBEDDING_MODEL`: Embedding model (default: nomic-embed-text)
- `INDEX_STORAGE_PATH`: Where to store the vector index (default: `/backend/storage`)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

**Endpoints**

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
    Ensure the project is compiled or has the `/target` folder populated
    Tip: Run `dbt docs generate`

3. Memory issues:
    - Smaller models like `llama2:7b` - depends on the machine
    - Reduce `chunk_size` in the configuration