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
            logger.info(f"Preprocessing legal text file: {file_path}")
            filename = os.path.basename(file_path)
            output_path = os.path.join(self.output_dir, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Initial cleanup
            content = re.sub(r"\r\n", "\n", content)  # Remove carriage returns
            content = re.sub(r"\n{3,}", "\n\n", content)  # Normalize newlines
            content = re.sub(r" +", " ", content)  # Normalize spaces
            content = re.sub(r"\.{3,}", "...", content)  # Normalize ellipsis
            content = re.sub(r"\.\.\.$", "", content)  # Remove trailing ellipsis

            # 1. Mark each chapter with a distinctive marker and ensure consistent formatting
            enhanced_content = re.sub(
                r"(\d+)\s*kap\.\s*([^§]*)",
                lambda m: f"\n\n=== KAPITEL {m.group(1)} ===\n{m.group(1)} kap. {m.group(2).strip()}",
                content,
            )

            # 2. Add chapter number before each paragraph with improved formatting
            def replace_paragraph(match):
                para_num = match.group(1)
                # Look for the most recent chapter reference before this paragraph
                text_before = enhanced_content[: match.start()]
                chapter_matches = list(re.finditer(r"(\d+)\s*kap\.", text_before))

                if chapter_matches:
                    # Get the most recent chapter number
                    latest_chapter = chapter_matches[-1].group(1)
                    # Return paragraph with chapter number in a consistent format
                    return f"\n\n{latest_chapter} kap, {para_num} §   "  # Added extra spaces for alignment
                else:
                    # If no chapter found, just return the paragraph with consistent spacing
                    return f"\n\n{para_num} §   "  # Added extra spaces for alignment

            # Apply our custom paragraph enhancement
            enhanced_content = re.sub(r"(\d+)\s*§", replace_paragraph, enhanced_content)

            # 3. Format headers and important sections with improved markers
            section_headers = [
                "Det patenterbara området",
                "Patent",
                "Europeiskt patent",
                "Patenterbara uppfinningar",
                "Människokroppen",
                "Växtsorter och djurraser",
                "Mönsterskydd",
                "Ensamrätt till mönster",
                "Skyddstiden",
            ]

            for header in section_headers:
                enhanced_content = re.sub(
                    rf"{re.escape(header)}",
                    f"\n\n--- {header.upper()} ---\n{header}",
                    enhanced_content,
                )

            # 4. Add section markers for improved chunking with consistent formatting
            section_markers = [
                "Grundläggande bestämmelser",
                "Lagens innehåll",
                "Lagens tillämpningsområde",
                "Svenskt patent",
                "Registrering av mönster",
                "Skyddsförutsättningar",
            ]

            for marker in section_markers:
                enhanced_content = re.sub(
                    rf"{re.escape(marker)}",
                    f"\n\n--- {marker.upper()} ---\n{marker}",
                    enhanced_content,
                )

            # 5. Final cleanup with improved formatting
            enhanced_content = re.sub(
                r"\n{3,}", "\n\n", enhanced_content
            )  # Remove extra newlines
            enhanced_content = re.sub(
                r" +", " ", enhanced_content
            )  # Remove extra spaces
            enhanced_content = re.sub(
                r"\.{3,}", "...", enhanced_content
            )  # Normalize ellipsis
            enhanced_content = re.sub(
                r"\.\.\.$", "", enhanced_content
            )  # Remove trailing ellipsis
            enhanced_content = (
                enhanced_content.strip()
            )  # Remove leading/trailing whitespace

            # 6. Ensure consistent spacing after paragraphs
            enhanced_content = re.sub(
                r"§\s+", "§   ", enhanced_content
            )  # Consistent spacing after §
            enhanced_content = re.sub(
                r"kap\.\s+", "kap. ", enhanced_content
            )  # Consistent spacing after kap.

            # Write the enhanced content to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(enhanced_content)

            logger.info(f"Preprocessed legal text saved to {output_path}")
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
