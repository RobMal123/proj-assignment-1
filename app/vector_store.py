from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.storage import StorageContext
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import os
import logging
import re
from app.config import VECTOR_STORE_DIR, PDF_PROCESSED_DIR, GEMINI_API_KEY, GEMINI_MODEL
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure embedding model to use a model that's good for technical and legal patent terminology
# Using BGE model which performs well on retrieval tasks
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
# Alternative options:
# - "sentence-transformers/all-mpnet-base-v2" (Higher quality but slower)
# - "sentence-transformers/multi-qa-mpnet-base-dot-v1" (Good for question answering)


class VectorStore:
    def __init__(self):
        """Initialize the vector store for document retrieval."""
        self.index = None
        # Ensure directories exist
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        os.makedirs(PDF_PROCESSED_DIR, exist_ok=True)

        # Initialize Gemini if API key is available
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            logger.info(
                f"Initialized Gemini model ({GEMINI_MODEL}) for query processing"
            )
        else:
            self.model = None
            logger.warning(
                "No Gemini API key found. Query processing won't be available."
            )

        self.load_or_create_index()

    def load_or_create_index(self):
        """Load existing index or create a new one if none exists."""
        try:
            if os.path.exists(VECTOR_STORE_DIR) and os.listdir(VECTOR_STORE_DIR):
                logger.info(f"Loading existing index from {VECTOR_STORE_DIR}")
                storage_context = StorageContext.from_defaults(
                    persist_dir=VECTOR_STORE_DIR
                )
                self.index = load_index_from_storage(storage_context)
            else:
                logger.info("No existing index found. Creating new index...")
                self.create_index()
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            logger.info("Creating new index...")
            self.create_index()

    def create_index(self):
        """Create a new index from processed documents with improved chunking for patent law texts."""
        if not os.path.exists(PDF_PROCESSED_DIR) or not os.listdir(PDF_PROCESSED_DIR):
            logger.warning(
                f"No documents found in {PDF_PROCESSED_DIR}. Index creation skipped."
            )
            return

        try:
            logger.info(f"Loading documents from {PDF_PROCESSED_DIR}")
            documents = SimpleDirectoryReader(PDF_PROCESSED_DIR).load_data()
            if not documents:
                logger.warning("No documents loaded from the directory")
                return

            # Create a custom chunker optimized for patent documents
            # - smaller chunk_size for better precision on specific paragraphs
            # - higher overlap to ensure context is maintained
            splitter = SentenceSplitter(
                chunk_size=384,  # Smaller chunks for more precise retrieval
                chunk_overlap=192,  # Higher overlap to preserve context
                paragraph_separator="\n\n",
            )

            logger.info(
                f"Creating index from {len(documents)} documents with patent-optimized chunking"
            )
            nodes = splitter.get_nodes_from_documents(documents)

            # For enhanced logging, count references to patents and key sections
            patent_references = 0
            section_references = 0
            important_sections = (
                0  # Count of chunks with 1 kap. 1 § and similar important sections
            )

            for node in nodes:
                if re.search(r"Patent|patent|uppfinn", node.text):
                    patent_references += 1
                if re.search(r"\d+\s*§", node.text):
                    section_references += 1
                # Specifically identify important sections like 1 kap. 1 §
                if re.search(
                    r"1\s*kap\.\s*1\s*§|ensamrätt|patenterbara",
                    node.text,
                    re.IGNORECASE,
                ):
                    important_sections += 1
                    # Add metadata to help with retrieval
                    if "metadata" in node.__dict__:
                        node.metadata["important"] = True

            logger.info(
                f"Created {len(nodes)} chunks, with {patent_references} chunks containing patent references, "
                f"{section_references} containing section references, and {important_sections} important sections"
            )

            self.index = VectorStoreIndex(nodes)
            self.persist_index()
            logger.info(f"Index created successfully with {len(nodes)} chunks")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def persist_index(self):
        """Save the index to disk."""
        if self.index:
            logger.info(f"Saving index to {VECTOR_STORE_DIR}")
            self.index.storage_context.persist(persist_dir=VECTOR_STORE_DIR)
            logger.info(f"Index saved to {VECTOR_STORE_DIR}")
        else:
            logger.warning("No index to persist")

    def query(self, query_text):
        """Query the vector store for relevant document chunks and generate response with Gemini."""
        if not self.index:
            logger.error("Cannot query - index is not loaded")
            return "Sorry, the document index is not available right now."

        try:
            # Check for specific section pattern queries (e.g., "1 kap. 1 §" or "1 paragraf")
            original_query = query_text
            section_match = re.search(
                r"(\d+)\s*(kap\.?|kapitel)\.?\s*(\d+)?\s*(?:§|paragraf)?",
                query_text,
                re.IGNORECASE,
            )
            paragraf_match = re.search(
                r"(\d+)\s*(?:§|paragraf)", query_text, re.IGNORECASE
            )

            # Enhanced the query with specific patterns if found
            if section_match:
                chap_num = section_match.group(1)
                para_num = section_match.group(3) if section_match.group(3) else ""
                if para_num:
                    enhanced_text = f"{chap_num} kap. {para_num} § {query_text}"
                else:
                    enhanced_text = f"{chap_num} kap. {query_text}"
                logger.info(f"Enhanced query with chapter reference: {enhanced_text}")
                query_text = enhanced_text
            elif paragraf_match:
                para_num = paragraf_match.group(1)
                # Check if "första kapitlet" or similar is in the query
                if re.search(
                    r"först(?:a)?(?:\s*kapitel|\s*kap\.?)", query_text, re.IGNORECASE
                ):
                    enhanced_text = f"1 kap. {para_num} § {query_text}"
                    logger.info(
                        f"Enhanced query with first chapter reference: {enhanced_text}"
                    )
                    query_text = enhanced_text

            # Look for specific patent law key concepts
            key_concepts = []
            for concept in [
                "ensamrätt",
                "patent",
                "uppfinning",
                "patenterbar",
                "människokropp",
            ]:
                if concept.lower() in query_text.lower():
                    key_concepts.append(concept)

            if key_concepts:
                logger.info(
                    f"Found key patent concepts in query: {', '.join(key_concepts)}"
                )

            # Configure query parameters
            query_kwargs = {
                "similarity_top_k": 8  # Retrieve more chunks for better context
            }

            logger.info(f"Querying index with enhanced query: {query_text}")

            # Get relevant context from the vector store
            query_engine = self.index.as_query_engine(**query_kwargs)
            retriever = query_engine.retriever
            nodes = retriever.retrieve(query_text)

            if not nodes:
                logger.warning("No relevant documents found in the index")
                context_texts = ["No relevant documents found"]
                source_nodes = []
            else:
                # Extract text and node info from retrieved nodes
                context_texts = [node.node.text for node in nodes]
                source_nodes = nodes
                logger.info(f"Retrieved {len(nodes)} relevant chunks from the index")

            # Format context for Gemini
            context_str = "\n\n".join(context_texts)

            # Check if Gemini is available
            if not self.model:
                logger.error("Gemini model not available - cannot generate response")
                return "Sorry, the Gemini model is not available. Please check your API key."

            # Generate response using Gemini with the retrieved context
            prompt = f"""Du är en juridisk assistent som svarar på frågor om svensk lagstiftning inom immaterialsrättlagstiftning, inklusive upphovsrätt, patenträtt, varumärkesrätt och mönsterskydd.
            Du ska svara **på svenska**. Använd endast informationen i den tillhandahållna lagtexten nedan. Om du inte hittar ett direkt svar, säg det tydligt och visa den mest relevanta informationen ändå.
            
            ### Viktigt:
            - Ange alltid exakt kapitel och paragraf när du hänvisar till lagtext (t.ex. "Enligt 1 kap. 2 §...")
            - Dubbelkolla NOGA att kapitel och paragraf hör ihop - kontrollera att du inte blandar paragrafnummer från ett kapitel med fel kapitelnummer
            - Om du citerar lagtext, markera tydligt början och slutet på citatet
            - Hänvisa alltid till ursprungskällan och var helt transparent med var informationen kommer ifrån
            - Om paragrafnummer och kapitelnummer förekommer separat i olika delar av texten, säkerställ att du kombinerar dem korrekt
            
            ### Lagtext:
            {context_str}

            ### Fråga:
            {query_text}

            Besvara frågan med direkt stöd i texten, utan egna antaganden. Du ska svara **på svenska**. Ange alltid kapitel- och paragrafnummer när det är relevant. Dubbelkolla att du inte anger fel kapitelnummer för en paragraf."""

            # Generate response with Gemini
            gemini_response = self.model.generate_content(prompt)

            # Create a response object with source information
            class EnhancedResponse:
                def __init__(self, text, source_nodes):
                    self.text = text
                    self.source_nodes = source_nodes

                def __str__(self):
                    return self.text

                def get_formatted_sources(self):
                    if not self.source_nodes:
                        return "Inga specifika källor matchade din fråga."

                    formatted_sources = []
                    for i, node in enumerate(self.source_nodes):
                        # Extract file name
                        file_name = "Okänd källa"
                        if (
                            hasattr(node.node, "metadata")
                            and "file_name" in node.node.metadata
                        ):
                            file_name = node.node.metadata["file_name"]

                        # Try to extract chapter and paragraph information with improved pattern matching
                        text = node.node.text

                        # Look for close proximity chapter-paragraph matches first (most reliable)
                        combined_match = re.search(r"(\d+)\s*kap\.\s*(\d+)\s*§", text)
                        if combined_match:
                            chapter_num = combined_match.group(1)
                            para_num = combined_match.group(2)
                            location_info = f" (kapitel {chapter_num}, § {para_num})"
                        else:
                            # If no combined match, look for separate matches
                            chapter_matches = re.findall(r"(\d+)\s*kap\.", text)
                            paragraph_matches = re.findall(r"(\d+)\s*§", text)

                            # If we have exactly one chapter and at least one paragraph, we can infer a relationship
                            if len(chapter_matches) == 1 and paragraph_matches:
                                chapter_info = f"kapitel {chapter_matches[0]}"
                                # Use the first paragraph as the most relevant
                                paragraph_info = f"§ {paragraph_matches[0]}"
                                location_info = f" ({chapter_info}, {paragraph_info})"
                            else:
                                # Otherwise provide whatever information we have
                                chapter_info = (
                                    f"kapitel {chapter_matches[0]}"
                                    if chapter_matches
                                    else ""
                                )
                                paragraph_info = (
                                    f"§ {paragraph_matches[0]}"
                                    if paragraph_matches
                                    else ""
                                )

                                if chapter_info and paragraph_info:
                                    location_info = (
                                        f" ({chapter_info}, {paragraph_info})"
                                    )
                                elif chapter_info:
                                    location_info = f" ({chapter_info})"
                                elif paragraph_info:
                                    location_info = f" ({paragraph_info})"
                                else:
                                    location_info = ""

                        # Format the source with similarity score and location info
                        formatted_sources.append(
                            f"Källa {i + 1}: {file_name}{location_info} (relevans: {node.score:.2f})"
                        )

                        # Add a small excerpt from the text to help verify correctness
                        text_excerpt = text[:150] + "..." if len(text) > 150 else text
                        formatted_sources.append(f'    Utdrag: "{text_excerpt}"')

                    return "\n".join(formatted_sources)

            return EnhancedResponse(gemini_response.text, source_nodes)

        except Exception as e:
            logger.error(f"Error querying index: {e}")

            # If we have a Gemini model, try a direct query as last resort
            if self.model:
                try:
                    logger.info("Attempting direct Gemini query as fallback")
                    direct_prompt = f"""Du är en juridisk assistent som svarar på frågor om svensk immaterialsrättlagstiftning, inklusive upphovsrätt, patenträtt, varumärkesrätt och mönsterskydd.
                    
                    Du ska svara **på svenska** och ange kapitel och paragraf när det är möjligt. 
                    
                    Fråga: {query_text}
                    
                    Var tydlig om du inte har tillräcklig information för att svara på frågan."""
                    direct_response = self.model.generate_content(direct_prompt)

                    class FallbackResponse:
                        def __init__(self, text):
                            self.text = text

                        def __str__(self):
                            return self.text

                        def get_formatted_sources(self):
                            return "Direkt svar från Gemini utan dokumentkontext på grund av indexeringsfel. Använder BGE inbäddningsmodell (BAAI/bge-small-en-v1.5)."

                    return FallbackResponse(direct_response.text)
                except Exception as fallback_e:
                    logger.error(f"Fallback response also failed: {fallback_e}")

            return f"Error processing query: {str(e)}"

    def refresh_index(self):
        """Refresh the index with the latest documents."""
        logger.info("Refreshing document index...")
        self.create_index()
        return "Index refreshed successfully"
