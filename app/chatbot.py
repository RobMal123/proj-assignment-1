import logging
import time
from app.vector_store import VectorStore
from app.config import GEMINI_API_KEY, GEMINI_MODEL
import google.generativeai as genai
from prometheus_client import Histogram, REGISTRY

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
            logger.info("Chatbot initialized with RAG capabilities using Gemini")
        else:
            self.model = None
            logger.warning(
                "No Gemini API key found. Chatbot will not be able to generate responses."
            )

    def get_response(self, query, conversation_history=None):
        """Generate a response to the user query using RAG."""
        if conversation_history is None:
            conversation_history = []

        start_time = time.time()
        logger.info(f"Processing query: {query}")

        try:
            # Check if API key is available
            if not GEMINI_API_KEY:
                raise ValueError("Gemini API key not found in environment variables")

            # Get relevant context from vector store
            rag_context = self.vector_store.query(query)
            context_str = str(rag_context)

            # Prepare chat history for Gemini
            # Convert from OpenAI format to Gemini chat format
            gemini_messages = []

            # Add system message with context
            system_prompt = f"You are a helpful assistant answering questions based on the following information: {context_str}. If you don't know the answer based on this information, say so."

            # Start a new chat with the system prompt
            chat = self.model.start_chat(history=[])

            # Add conversation history
            for message in conversation_history[
                -5:
            ]:  # Only use last 5 messages for context
                role = message.get("role", "")
                content = message.get("content", "")

                if role == "user":
                    gemini_messages.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    gemini_messages.append({"role": "model", "parts": [content]})

            # Add current query with context
            prompt = f"Context: {context_str}\n\nQuestion: {query}"

            # Generate response using Gemini
            response = chat.send_message(prompt)

            # Extract token usage - Gemini doesn't provide token count directly
            # We'll estimate based on characters
            estimated_tokens = len(prompt) / 4  # Rough estimate
            if TOKEN_USAGE:
                TOKEN_USAGE.observe(estimated_tokens)
            logger.info(f"Estimated token usage: {estimated_tokens}")

            answer = response.text

            # Log response time
            elapsed_time = time.time() - start_time
            logger.info(f"Response generated in {elapsed_time:.2f} seconds")

            return {
                "answer": answer,
                "sources": str(rag_context.get_formatted_sources())
                if hasattr(rag_context, "get_formatted_sources")
                else "",
                "response_time": elapsed_time,
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "answer": "I'm sorry, I encountered an error processing your request.",
                "error": str(e),
                "response_time": time.time() - start_time,
            }

    def refresh_knowledge(self):
        """Refresh the knowledge base with latest documents."""
        return self.vector_store.refresh_index()
