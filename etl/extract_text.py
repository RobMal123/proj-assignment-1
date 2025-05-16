import os
import PyPDF2
import logging
import pandas as pd
import time
import re
from app.config import PDF_SOURCE_DIR, PDF_PROCESSED_DIR

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Extracts and preprocesses text from PDF files."""

    def __init__(self, input_dir=None, output_dir=None):
        """
        Initialize the PDF processor.

        Args:
            input_dir (str): Directory containing source PDFs
            output_dir (str): Directory to save processed text files
        """
        self.input_dir = input_dir or PDF_SOURCE_DIR
        self.output_dir = output_dir or PDF_PROCESSED_DIR

        # Create directories if they don't exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a PDF file.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            list: List of pages, where each page is the extracted text
        """
        try:
            start_time = time.time()
            logger.info(f"Extracting text from {pdf_path}")

            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                pages = []

                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            pages.append(text)
                        else:
                            logger.warning(
                                f"No text extracted from page {i + 1} in {pdf_path}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error extracting text from page {i + 1} in {pdf_path}: {str(e)}"
                        )

            process_time = time.time() - start_time
            logger.info(
                f"Extracted text from {len(pages)} pages in {process_time:.2f} seconds"
            )

            return pages

        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return []

    def preprocess_text(self, text):
        """
        Preprocess the extracted text.

        Args:
            text (str): Raw text from PDF

        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        processed = re.sub(r"\s+", " ", text)

        # Remove page numbers (common formats)
        processed = re.sub(r"\b\d+\s*\|\s*Page\b", "", processed)
        processed = re.sub(r"\bPage\s*\d+\s*of\s*\d+\b", "", processed)

        # Remove headers/footers (customize as needed)
        processed = re.sub(r"^.*CONFIDENTIAL.*$", "", processed, flags=re.MULTILINE)

        # Remove special characters but keep basic punctuation
        processed = re.sub(r'[^\w\s.,;:!?()\[\]{}\-–—\'\""]', " ", processed)

        # Fix hyphenated words split across lines
        processed = re.sub(r"(\w+)-\s*(\w+)", r"\1\2", processed)

        return processed.strip()

    def process_pdf(self, pdf_path):
        """
        Process a single PDF file and save the extracted text.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            str: Path to the processed text file, or None if processing failed
        """
        try:
            # Extract text from PDF
            pages = self.extract_text_from_pdf(pdf_path)

            if not pages:
                logger.warning(f"No text extracted from {pdf_path}")
                return None

            # Preprocess each page
            processed_pages = [self.preprocess_text(page) for page in pages]

            # Create output filename
            pdf_filename = os.path.basename(pdf_path)
            txt_filename = os.path.splitext(pdf_filename)[0] + ".txt"
            output_path = os.path.join(self.output_dir, txt_filename)

            # Write processed text to file
            with open(output_path, "w", encoding="utf-8") as f:
                for i, page in enumerate(processed_pages):
                    f.write(f"--- Page {i + 1} ---\n")
                    f.write(page)
                    f.write("\n\n")

            logger.info(f"Processed PDF saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return None

    def process_all_pdfs(self):
        """
        Process all PDF files in the input directory.

        Returns:
            list: List of processed text file paths
        """
        processed_files = []

        # Get all PDF files in the input directory
        pdf_files = [
            f for f in os.listdir(self.input_dir) if f.lower().endswith(".pdf")
        ]

        if not pdf_files:
            logger.warning(f"No PDF files found in {self.input_dir}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        # Process each PDF
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.input_dir, pdf_file)
            result = self.process_pdf(pdf_path)

            if result:
                processed_files.append(result)

        logger.info(f"Processed {len(processed_files)} of {len(pdf_files)} PDF files")
        return processed_files

    def generate_metadata_csv(self, processed_files):
        """
        Generate a CSV file with metadata about processed documents.

        Args:
            processed_files (list): List of processed text file paths

        Returns:
            str: Path to the metadata CSV file
        """
        metadata = []

        for file_path in processed_files:
            try:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)

                # Count lines and pages
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    pages = content.count("--- Page")

                metadata.append(
                    {
                        "file_name": file_name,
                        "file_path": file_path,
                        "file_size_kb": file_size / 1024,
                        "pages": pages,
                        "lines": lines,
                        "processed_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            except Exception as e:
                logger.error(f"Error generating metadata for {file_path}: {str(e)}")

        # Create DataFrame and save as CSV
        if metadata:
            df = pd.DataFrame(metadata)
            csv_path = os.path.join(self.output_dir, "document_metadata.csv")
            df.to_csv(csv_path, index=False)
            logger.info(f"Metadata saved to {csv_path}")
            return csv_path
        else:
            logger.warning("No metadata generated")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    processor = PDFProcessor()
    processed_files = processor.process_all_pdfs()

    if processed_files:
        processor.generate_metadata_csv(processed_files)
