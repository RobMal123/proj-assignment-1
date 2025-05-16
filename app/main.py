from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import time
from app.chatbot import Chatbot
from app.config import APP_HOST, APP_PORT, DEBUG, ENABLE_METRICS
import uvicorn
from prometheus_client import make_asgi_app

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Helpdesk Chatbot",
    description="A chatbot that answers questions based on PDF knowledge base",
    version="1.0.0",
    debug=DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add prometheus metrics
if ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    logger.info("Prometheus metrics enabled at /metrics endpoint")


# Function to get or create a chatbot instance
# This makes it easier to mock in tests
def get_chatbot():
    # Create a singleton chatbot instance
    if not hasattr(get_chatbot, "instance") or get_chatbot.instance is None:
        get_chatbot.instance = Chatbot()
    return get_chatbot.instance


# Define request and response models
class ChatRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[str] = None
    response_time: float


@app.get("/")
async def root():
    """Root endpoint with basic info about the API."""
    return {
        "message": "AI Helpdesk Chatbot API",
        "endpoints": {
            "/chat": "POST - Send a query to the chatbot",
            "/health": "GET - Check API health",
            "/refresh": "POST - Refresh knowledge base",
        },
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, chatbot: Chatbot = Depends(get_chatbot)):
    """Process a chat request and return the response."""
    logger.info(f"Received chat request: {request.query}")
    start_time = time.time()

    try:
        response = chatbot.get_response(request.query, request.conversation_history)
        logger.info(
            f"Chat response generated in {time.time() - start_time:.2f} seconds"
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Check the health of the API."""
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/refresh")
async def refresh_knowledge(
    background_tasks: BackgroundTasks, chatbot: Chatbot = Depends(get_chatbot)
):
    """Refresh the knowledge base in the background."""
    logger.info("Knowledge base refresh requested")
    background_tasks.add_task(chatbot.refresh_knowledge)
    return {
        "status": "refresh started",
        "message": "Knowledge base refresh has been started in the background",
    }


if __name__ == "__main__":
    logger.info(f"Starting server on {APP_HOST}:{APP_PORT}")
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=DEBUG)
