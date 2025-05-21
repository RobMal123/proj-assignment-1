# Legal Document RAG Chatbot (swedish)

Implementation of a Retrieval Augmented Generation (RAG) chatbot using Google Gemini API and LlamaIndex, specifically optimized for Swedish legal documents.

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
  ├── extract_text.py - Extract text from PDFs
  └── preprocess_text.py - Enhanced legal text preprocessing
📁 tools/          - Utility scripts
  ├── optimize_legal_text.py - Legal text optimization tool
  ├── test_query.py - Query testing and validation
  └── upload_pdf.py - PDF processing wrapper script
```

## Features

- **Enhanced Legal Text Processing**:

  - Consistent chapter and paragraph formatting
  - Clear section markers and headers
  - Improved text cleaning and normalization
  - Better handling of legal terminology

- **Improved Source Formatting**:

  - Clear chapter and paragraph references
  - Consistent spacing and alignment
  - Better readability of legal documents

- **Testing and Validation**:
  - Query testing tool for response validation
  - Predefined test queries
  - Response quality assessment

## Setup

1. Install the required packages:

   ```bash
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

   ```

3. Process your legal documents:

   a. Place your text files in the `data/raw` directory

   b. Run the preprocessing script:

   ```bash
   py -m etl.preprocess_text
   ```

   c. For PDF processing, you can:

   - Place PDF files directly in the `data/raw` directory
   - Download PDFs from a URL:
     ```bash
     py tools/upload_pdf.py --url https://example.com/document.pdf
     ```
   - Process existing PDFs:
     ```bash
     py tools/upload_pdf.py
     ```

4. Start the FastAPI server:

   ```bash
   py -m app.main
   ```

5. Open your browser and go to http://localhost:8000 to interact with the API.

## How It Works

1. Legal documents are processed through the ETL pipeline:

   - Text is extracted from PDFs
   - Legal text is preprocessed with enhanced formatting
   - Documents are cleaned and normalized

2. Processed text is embedded and stored in a vector database using LlamaIndex

3. When a user asks a question:
   - The most relevant document chunks are retrieved
   - The Google Gemini model generates a response using the retrieved context
   - Sources are formatted for better readability

## API Endpoints

- `POST /chat`: Send a query to the chatbot
- `GET /health`: Check API health
- `POST /refresh`: Refresh the knowledge base

## Testing

You can test the system's responses using the test_query.py tool:

```bash
# Test a single query
py tools/test_query.py "Your question here"

# Run all predefined test queries
py tools/test_query.py --all
```

## Example Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "What is the definition of a patent?"}
)

print(response.json())
```
