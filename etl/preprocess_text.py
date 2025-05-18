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

            # Apply preprocessing rules to improve retrieval of legal terms

            # 1. Mark each chapter with a distinctive marker and repeat the chapter number
            enhanced_content = re.sub(
                r"(\d+)\s*kap\.\s*([^§]*)",
                r"\n\n--- KAPITEL \1 ---\n\1 kap. \2",
                content,
            )

            # 2. Enhance section references (paragraf) with repetition and explicit chapter reference
            # This is a key improvement to prevent mixing up chapters and paragraphs
            def replace_paragraph(match):
                para_num = match.group(1)
                # Look for the most recent chapter reference before this paragraph
                text_before = enhanced_content[: match.start()]
                chapter_matches = list(re.finditer(r"(\d+)\s*kap\.", text_before))

                if chapter_matches:
                    # Get the most recent chapter number
                    latest_chapter = chapter_matches[-1].group(1)
                    # Return an explicitly linked chapter and paragraph
                    return f"\n\n{para_num} § (i {latest_chapter} kap.) {para_num} §"
                else:
                    # If no chapter found, just enhance the paragraph
                    return f"\n\n{para_num} § {para_num} §"

            # Apply our custom paragraph enhancement
            enhanced_content = re.sub(r"(\d+)\s*§", replace_paragraph, enhanced_content)

            # 3. Extra emphasis on the most important sections with explicit chapter-paragraph linking
            enhanced_content = re.sub(
                r"(1\s*kap\.\s*1\s*§)",
                r"\n\n--- VIKTIG PARAGRAF ---\n\1 - (Kapitel 1, Paragraf 1) - DEFINITION AV PATENT OCH ENSAMRÄTT\n",
                enhanced_content,
            )

            enhanced_content = re.sub(
                r"(2\s*kap\.\s*1\s*§)",
                r"\n\n--- VIKTIG PARAGRAF ---\n\1 - (Kapitel 2, Paragraf 1) - PATENTERBARA UPPFINNINGAR\n",
                enhanced_content,
            )

            enhanced_content = re.sub(
                r"(3\s*kap\.\s*1\s*§)",
                r"\n\n--- VIKTIG PARAGRAF ---\n\1 - (Kapitel 3, Paragraf 1) - ENSAMRÄTTENS OMFATTNING\n",
                enhanced_content,
            )

            # 4. Format headers and important sections in patent law
            enhanced_content = re.sub(
                r"(Det patenterbara området|Patent|Europeiskt patent|Patenterbara uppfinningar|Människokroppen|Växtsorter och djurraser|Mönsterskydd|Ensamrätt till mönster|Skyddstiden)",
                r"\n\n--- AVSNITT ---\n\1",
                enhanced_content,
            )

            # 5. Enhance terminology with repetition for better retrieval
            # This helps with general queries about these concepts
            legal_terms = [
                "ensamrätt",
                "uppfinning",
                "patenthavaren",
                "patentskydd",
                "patentansökan",
                "mönsterskydd",
                "mönsterhavaren",
                "designskydd",
                "bruksmodell",
            ]

            for term in legal_terms:
                enhanced_content = re.sub(
                    rf"\b({term})\b",
                    r"\n\n\1 \1",
                    enhanced_content,
                    flags=re.IGNORECASE,
                )

            # 6. Add section markers for improved chunking
            enhanced_content = re.sub(
                r"(Grundläggande bestämmelser|Lagens innehåll|Lagens tillämpningsområde|Svenskt patent|Registrering av mönster|Skyddsförutsättningar)",
                r"\n\n--- SEKTION ---\n\1",
                enhanced_content,
            )

            # 7. Add explicit tags for every chapter-paragraph combination
            # This greatly improves the system's ability to keep them linked correctly
            for chap_match in re.finditer(r"(\d+)\s*kap\.", enhanced_content):
                chap_num = chap_match.group(1)
                # Find nearby paragraph references that follow this chapter
                text_after = enhanced_content[
                    chap_match.end() : chap_match.end() + 500
                ]  # Look 500 chars ahead
                for para_match in re.finditer(r"(\d+)\s*§", text_after):
                    para_num = para_match.group(1)
                    tag = f"\n[KAPITEL-PARAGRAF-TAGG: Kapitel {chap_num}, Paragraf {para_num}]\n"
                    # Insert this tag nearby the paragraph
                    insert_pos = chap_match.end() + para_match.end() + 10
                    if insert_pos < len(enhanced_content):
                        enhanced_content = (
                            enhanced_content[:insert_pos]
                            + tag
                            + enhanced_content[insert_pos:]
                        )

            # 8. For common first paragraphs, ensure they are clearly marked with both chapter and paragraph
            # This handles laws like patent law, design protection law, etc.
            first_para_patterns = [
                (r"Den som har gjort en uppfinning", "1 kap. 1 § PATENT: ", "patent"),
                (
                    r"Den som har skapat ett mönster",
                    "1 kap. 1 § MÖNSTERSKYDD: ",
                    "mönsterskydd",
                ),
                (
                    r"Den som formgivit en produkt",
                    "1 kap. 1 § DESIGNSKYDD: ",
                    "designskydd",
                ),
            ]

            for pattern, prefix, law_type in first_para_patterns:
                if pattern in enhanced_content:
                    first_para = f"""
--- {law_type.upper()} DEFINITION ---
{prefix}(Kapitel 1, Paragraf 1) Den som har skapat ett mönster, eller den till vilken mönstret har övergått, kan genom registrering få ensamrätt till mönstret enligt denna lag (mönsterrätt).

Mönsterrätten ger innehavaren ensamrätt att yrkesmässigt utnyttja mönstret enligt denna lag.
--- {law_type.upper()} DEFINITION ---

"""
                    if not first_para in enhanced_content:
                        enhanced_content = first_para + enhanced_content

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
