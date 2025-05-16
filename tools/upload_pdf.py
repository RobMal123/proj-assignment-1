#!/usr/bin/env python
"""
Simple script to process PDFs into text for the RAG chatbot.
Leverages existing ETL functionality.
"""

import os
import sys
import logging

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.extract_text import PDFProcessor
from etl.download_pdfs import PDFDownloader
from app.vector_store import VectorStore
from app.config import PDF_SOURCE_DIR, PDF_PROCESSED_DIR, VECTOR_STORE_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_local_pdfs():
    """Process PDFs from the local data/raw directory"""
    logger.info("Processing local PDFs...")

    # Ensure directories exist
    os.makedirs(PDF_SOURCE_DIR, exist_ok=True)
    os.makedirs(PDF_PROCESSED_DIR, exist_ok=True)

    # Check if there are PDF files in the source directory
    pdf_files = [f for f in os.listdir(PDF_SOURCE_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.warning(f"No PDF files found in {PDF_SOURCE_DIR}")
        return []

    logger.info(f"Found {len(pdf_files)} PDF files in {PDF_SOURCE_DIR}")

    processor = PDFProcessor()
    processed_files = processor.process_all_pdfs()
    logger.info(f"Processed {len(processed_files)} PDF files")
    return processed_files


def download_pdf_from_url(url):
    """Download a PDF from a URL"""
    logger.info(f"Downloading PDF from {url}...")

    # Ensure directory exists
    os.makedirs(PDF_SOURCE_DIR, exist_ok=True)

    downloader = PDFDownloader()
    success = downloader.download_pdf(url)
    if success:
        logger.info(f"Successfully downloaded PDF from {url}")
        return True
    else:
        logger.error(f"Failed to download PDF from {url}")
        return False


def refresh_vector_store():
    """Refresh the vector store with the processed files"""
    logger.info("Refreshing vector store...")

    # Ensure directory exists
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    vector_store = VectorStore()
    vector_store.create_index()

    # Verify files were created
    if os.path.exists(VECTOR_STORE_DIR) and os.listdir(VECTOR_STORE_DIR):
        logger.info(f"Vector store created successfully at {VECTOR_STORE_DIR}")
    else:
        logger.warning(f"No files were created in {VECTOR_STORE_DIR}")

    return True


def main():
    """Main entry point for the script"""
    import argparse

    parser = argparse.ArgumentParser(description="Process PDFs for RAG chatbot")
    parser.add_argument("--url", help="Download PDF from URL")
    args = parser.parse_args()

    if args.url:
        if download_pdf_from_url(args.url):
            process_local_pdfs()
            refresh_vector_store()
    else:
        # Just process local PDFs
        processed_files = process_local_pdfs()
        if processed_files:
            refresh_vector_store()
        else:
            logger.warning("No PDFs were processed, skipping vector store refresh")

    logger.info("PDF processing complete")


if __name__ == "__main__":
    main()
