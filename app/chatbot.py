import logging
import time
from app.vector_store import VectorStore
from app.config import GEMINI_API_KEY, GEMINI_MODEL
import google.generativeai as genai
from prometheus_client import Histogram, REGISTRY
from typing import Optional, List, Dict

# Setup logging
logger = logging.getLogger(__name__)

# Flag to track if metrics have been initialized
_metrics_initialized = False

# Metrics placeholders
RESPONSE_TIME = None
TOKEN_USAGE = None


def initialize_metrics():
    """Initialize Prometheus metrics if not already done"""
    global RESPONSE_TIME, TOKEN_USAGE, _metrics_initialized

    if _metrics_initialized:
        return

    # Check if metrics already exist in registry to avoid duplicates
    existing_metrics = set()
    for collector in REGISTRY._names_to_collectors.values():
        if hasattr(collector, "name"):
            existing_metrics.add(collector.name)

    # Only create metrics if they don't already exist
    if "chatbot_response_time_seconds" not in existing_metrics:
        RESPONSE_TIME = Histogram(
            "chatbot_response_time_seconds", "Time spent generating chatbot response"
        )
    else:
        # Find existing metric from registry
        for collector in REGISTRY._names_to_collectors.values():
            if (
                hasattr(collector, "name")
                and collector.name == "chatbot_response_time_seconds"
            ):
                RESPONSE_TIME = collector
                break

    if "chatbot_token_usage" not in existing_metrics:
        TOKEN_USAGE = Histogram(
            "chatbot_token_usage", "Number of tokens used per request"
        )
    else:
        # Find existing metric from registry
        for collector in REGISTRY._names_to_collectors.values():
            if hasattr(collector, "name") and collector.name == "chatbot_token_usage":
                TOKEN_USAGE = collector
                break

    _metrics_initialized = True


# Initialize metrics
initialize_metrics()


class Chatbot:
    def __init__(self):
        """Initialize the chatbot with vector store for RAG."""
        self.vector_store = VectorStore()

        # Only configure Gemini if API key is available
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            logger.info(
                f"Chatbot initialized with RAG capabilities using Gemini ({GEMINI_MODEL})"
            )
        else:
            self.model = None
            logger.warning(
                "No Gemini API key found. Chatbot will not be able to generate responses."
            )

    def get_response(
        self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict:
        """Get a response from the chatbot using RAG."""
        logger.info(f"Processing query: {query}")
        start_time = time.time()

        try:
            # Get response from vector store
            response = self.vector_store.query(query)

            # Format sources for the response
            sources = []
            if hasattr(response, "used_sources") and response.used_sources:
                for node in response.used_sources:
                    source = {
                        "file": node.node.metadata.get("file_name", "Unknown"),
                        "text": node.node.text[:200] + "..."
                        if len(node.node.text) > 200
                        else node.node.text,
                        "relevance": float(node.score),
                    }
                    sources.append(source)

            return {
                "answer": str(response),
                "sources": sources,
                "response_time": time.time() - start_time,
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def refresh_knowledge(self):
        """Refresh the knowledge base with latest documents."""
        return self.vector_store.refresh_index()
