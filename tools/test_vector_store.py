#!/usr/bin/env python
"""
Test script to check vector store functionality.
"""

import os
import sys
import logging

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.vector_store import VectorStore
from app.config import PDF_SOURCE_DIR, PDF_PROCESSED_DIR, VECTOR_STORE_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_vector_store():
    """Test the vector store functionality"""

    # Print directory information
    logger.info(f"PDF source directory: {PDF_SOURCE_DIR}")
    logger.info(f"PDF processed directory: {PDF_PROCESSED_DIR}")
    logger.info(f"Vector store directory: {VECTOR_STORE_DIR}")

    # Check if directories exist
    logger.info(f"PDF source directory exists: {os.path.exists(PDF_SOURCE_DIR)}")
    logger.info(f"PDF processed directory exists: {os.path.exists(PDF_PROCESSED_DIR)}")
    logger.info(f"Vector store directory exists: {os.path.exists(VECTOR_STORE_DIR)}")

    # Check for files in directories
    if os.path.exists(PDF_SOURCE_DIR):
        pdf_files = [
            f for f in os.listdir(PDF_SOURCE_DIR) if f.lower().endswith(".pdf")
        ]
        logger.info(f"PDF files in source directory: {len(pdf_files)}")
        if pdf_files:
            logger.info(f"Sample PDF files: {pdf_files[:3]}")

    if os.path.exists(PDF_PROCESSED_DIR):
        txt_files = [
            f for f in os.listdir(PDF_PROCESSED_DIR) if f.lower().endswith(".txt")
        ]
        logger.info(f"Text files in processed directory: {len(txt_files)}")
        if txt_files:
            logger.info(f"Sample text files: {txt_files[:3]}")

    if os.path.exists(VECTOR_STORE_DIR):
        vector_files = os.listdir(VECTOR_STORE_DIR)
        logger.info(f"Files in vector store directory: {len(vector_files)}")
        if vector_files:
            logger.info(f"Sample vector files: {vector_files[:5]}")

    # Test creating a vector store
    logger.info("Creating a vector store...")
    vector_store = VectorStore()

    # Try to create an index (this will only work if there are processed files)
    if os.path.exists(PDF_PROCESSED_DIR) and os.listdir(PDF_PROCESSED_DIR):
        logger.info("Creating index from processed files...")
        vector_store.create_index()

        # Check if vector store files were created
        if os.path.exists(VECTOR_STORE_DIR) and os.listdir(VECTOR_STORE_DIR):
            logger.info(
                f"Vector store created successfully with files: {os.listdir(VECTOR_STORE_DIR)}"
            )
        else:
            logger.warning("No files were created in the vector store directory")
    else:
        logger.warning("No processed files found, skipping index creation")

    logger.info("Vector store test complete")


if __name__ == "__main__":
    test_vector_store()
