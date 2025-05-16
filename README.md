# Simple RAG Chatbot

Implementation of a Retrieval Augmented Generation (RAG) chatbot using Google Gemini API and LlamaIndex.

## Project Structure

```
📁 app/            - Core application code
  ├── chatbot.py   - RAG chatbot implementation
  ├── config.py    - Configuration settings
  ├── main.py      - FastAPI server
  └── vector_store.py - Document embeddings and vector storage
📁 data/           - Data directories
  ├── raw/         - Original PDF documents
  ├── processed/   - Extracted text from PDFs
  └── vector_store/ - Vector embeddings
📁 etl/            - ETL processing scripts
  ├── download_pdfs.py - Download PDFs from URLs
  └── extract_text.py - Extract text from PDFs
📁 tools/          - Utility scripts
  └── upload_pdf.py - Simple PDF processing wrapper script
```

## Setup

1. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Gemini API key:

   ```
   # Google Gemini API
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-lite

   # Server Configuration
   APP_HOST=0.0.0.0
   APP_PORT=8000
   DEBUG=False

   # Monitoring
   ENABLE_METRICS=True
   LOG_LEVEL=INFO
   ```

3. Process PDFs by either:

   - Placing PDF files directly in the `data/raw` directory
   - Downloading PDFs from a URL:
     ```
     python tools/upload_pdf.py --url https://example.com/document.pdf
     ```
   - Processing existing PDFs in the raw directory:
     ```
     python tools/upload_pdf.py
     ```

4. Start the FastAPI server:

   ```
   python -m app.main
   ```

5. Open your browser and go to http://localhost:8000 to interact with the API.

## How It Works

1. PDF documents are processed to extract text using the ETL pipeline.
2. Text is embedded and stored in a vector database using LlamaIndex.
3. When a user asks a question, the most relevant document chunks are retrieved.
4. The Google Gemini model generates a response using the retrieved context.

## API Endpoints

- `POST /chat`: Send a query to the chatbot
- `GET /health`: Check API health
- `POST /refresh`: Refresh the knowledge base

## Example Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "What is RAG?"}
)

print(response.json())
```
