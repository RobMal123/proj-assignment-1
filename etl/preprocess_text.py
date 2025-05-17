import os
import re
import logging
import shutil
from app.config import PDF_SOURCE_DIR, PDF_PROCESSED_DIR

logger = logging.getLogger(__name__)


class LegalTextProcessor:
    """Preprocesses Swedish patent law text files to optimize for retrieval."""

    def __init__(self, input_dir=None, output_dir=None):
        """
        Initialize the text processor.

        Args:
            input_dir (str): Directory containing source text files
            output_dir (str): Directory to save processed text files
        """
        self.input_dir = input_dir or PDF_SOURCE_DIR
        self.output_dir = output_dir or PDF_PROCESSED_DIR

        # Create directories if they don't exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def preprocess_legal_text(self, file_path):
        """
        Preprocess a Swedish patent law text file to optimize for retrieval.

        Args:
            file_path (str): Path to the text file

        Returns:
            str: Path to the processed file, or None if processing failed
        """
        try:
            logger.info(f"Preprocessing patent law text file: {file_path}")
            filename = os.path.basename(file_path)
            output_path = os.path.join(self.output_dir, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply preprocessing rules to improve retrieval of patent law terms

            # 1. Mark each chapter with a distinctive marker and repeat the chapter number
            enhanced_content = re.sub(
                r"(\d+)\s*kap\.\s*([^§]*)",
                r"\n\n--- KAPITEL \1 ---\n\1 kap. \2",
                content,
            )

            # 2. Enhance section references (paragraf) with repetition for emphasis
            enhanced_content = re.sub(r"(\d+)\s*§", r"\n\n\1 § \1 §", enhanced_content)

            # 3. Extra emphasis on the most important sections (1 kap. 1 §, etc.)
            # This is crucial for questions about specific sections
            enhanced_content = re.sub(
                r"(1\s*kap\.\s*1\s*§)",
                r"\n\n--- VIKTIG PARAGRAF ---\n\1 - DEFINITION AV PATENT OCH ENSAMRÄTT\n",
                enhanced_content,
            )

            enhanced_content = re.sub(
                r"(2\s*kap\.\s*1\s*§)",
                r"\n\n--- VIKTIG PARAGRAF ---\n\1 - PATENTERBARA UPPFINNINGAR\n",
                enhanced_content,
            )

            enhanced_content = re.sub(
                r"(3\s*kap\.\s*1\s*§)",
                r"\n\n--- VIKTIG PARAGRAF ---\n\1 - ENSAMRÄTTENS OMFATTNING\n",
                enhanced_content,
            )

            # 4. Format headers and important sections in patent law
            enhanced_content = re.sub(
                r"(Det patenterbara området|Patent|Europeiskt patent|Patenterbara uppfinningar|Människokroppen|Växtsorter och djurraser)",
                r"\n\n--- AVSNITT ---\n\1",
                enhanced_content,
            )

            # 5. Enhance patent terminology with repetition for better retrieval
            # This helps with general queries about these concepts
            for term in [
                "ensamrätt",
                "uppfinning",
                "patenthavaren",
                "patentskydd",
                "patentansökan",
            ]:
                enhanced_content = re.sub(
                    rf"\b({term})\b",
                    r"\n\n\1 \1",
                    enhanced_content,
                    flags=re.IGNORECASE,
                )

            # 6. Add section markers for improved chunking
            enhanced_content = re.sub(
                r"(Grundläggande bestämmelser|Lagens innehåll|Lagens tillämpningsområde|Svenskt patent)",
                r"\n\n--- SEKTION ---\n\1",
                enhanced_content,
            )

            # 7. Duplicate the first paragraph of the law which defines patents
            # This is the most commonly queried information
            if "Den som har gjort en uppfinning" in enhanced_content:
                first_para = """
--- PATENT DEFINITION ---
1 kap. 1 § PATENT: Den som har gjort en uppfinning, eller den till vilken uppfinnarens rätt har övergått, kan beviljas patent på uppfinningen i Sverige.

Ett patent ger patenthavaren ensamrätt att yrkesmässigt utnyttja uppfinningen enligt denna lag.
--- PATENT DEFINITION ---

"""
                enhanced_content = first_para + enhanced_content

            # Write the enhanced content to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(enhanced_content)

            logger.info(f"Preprocessed patent law text saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error preprocessing text file {file_path}: {str(e)}")
            return None

    def process_all_text_files(self):
        """
        Process all text files in the input directory.

        Returns:
            list: List of processed file paths
        """
        processed_files = []

        # Get all text files in the input directory
        text_files = [
            f for f in os.listdir(self.input_dir) if f.lower().endswith(".txt")
        ]

        if not text_files:
            logger.warning(f"No text files found in {self.input_dir}")
            return []

        logger.info(f"Found {len(text_files)} text files to process")

        # Process each text file
        for text_file in text_files:
            input_path = os.path.join(self.input_dir, text_file)
            result = self.preprocess_legal_text(input_path)

            if result:
                processed_files.append(result)

        logger.info(f"Processed {len(processed_files)} of {len(text_files)} text files")
        return processed_files

    def copy_existing_text_files(self):
        """
        Copy existing text files from raw to processed directory without preprocessing.

        Returns:
            list: List of copied file paths
        """
        copied_files = []

        # Get all text files in the input directory
        text_files = [
            f for f in os.listdir(self.input_dir) if f.lower().endswith(".txt")
        ]

        if not text_files:
            logger.warning(f"No text files found in {self.input_dir}")
            return []

        logger.info(f"Found {len(text_files)} text files to copy")

        # Copy each text file
        for text_file in text_files:
            try:
                input_path = os.path.join(self.input_dir, text_file)
                output_path = os.path.join(self.output_dir, text_file)

                shutil.copy2(input_path, output_path)
                copied_files.append(output_path)
                logger.info(f"Copied {text_file} to processed directory")

            except Exception as e:
                logger.error(f"Error copying {text_file}: {str(e)}")

        return copied_files


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    processor = LegalTextProcessor()
    # Choose the processing method:
    # 1. With preprocessing (recommended for better retrieval)
    processed_files = processor.process_all_text_files()
    # 2. Without preprocessing (simple copy)
    # processed_files = processor.copy_existing_text_files()

    if processed_files:
        logger.info(f"Successfully processed {len(processed_files)} files")
        logger.info(
            "Run the application with the /refresh endpoint to update the index"
        )
