import os
import requests
import logging
import time
from urllib.parse import urlparse
from datetime import datetime
from app.config import PDF_SOURCE_DIR, ETL_DOWNLOAD_TIMEOUT

logger = logging.getLogger(__name__)


class PDFDownloader:
    """Downloads PDF files from various sources."""

    def __init__(self, output_dir=None):
        """
        Initialize the PDF downloader.

        Args:
            output_dir (str): Directory to save downloaded PDFs
        """
        self.output_dir = output_dir or PDF_SOURCE_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def download_from_url(self, url, filename=None, timeout=None):
        """
        Download a PDF from a URL.

        Args:
            url (str): URL of the PDF to download
            filename (str): Optional filename to save the PDF as
            timeout (int): Request timeout in seconds

        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        timeout = timeout or ETL_DOWNLOAD_TIMEOUT

        try:
            start_time = time.time()
            logger.info(f"Downloading PDF from {url}")

            # Create a filename if not provided
            if not filename:
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.split("/")
                filename = next(
                    (part for part in reversed(path_parts) if part), "document.pdf"
                )

                # Add timestamp to avoid overwriting
                if not filename.endswith(".pdf"):
                    filename += ".pdf"
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{timestamp}_{filename}"

            output_path = os.path.join(self.output_dir, filename)

            # Stream the download to handle large files
            with requests.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()

                # Check if it's actually a PDF
                content_type = response.headers.get("Content-Type", "")
                if "application/pdf" not in content_type and not url.endswith(".pdf"):
                    logger.warning(f"URL does not appear to be a PDF: {content_type}")

                # Save the file
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

            download_time = time.time() - start_time
            file_size = os.path.getsize(output_path) / 1024  # KB
            logger.info(
                f"Downloaded {filename} ({file_size:.1f} KB) in {download_time:.2f} seconds"
            )

            return output_path

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF from {url}: {str(e)}")
            return None

    def download_from_list(self, url_list):
        """
        Download multiple PDFs from a list of URLs.

        Args:
            url_list (list): List of URLs to download

        Returns:
            list: List of successfully downloaded file paths
        """
        successful_downloads = []

        for url in url_list:
            try:
                result = self.download_from_url(url)
                if result:
                    successful_downloads.append(result)
            except Exception as e:
                logger.error(f"Error downloading {url}: {str(e)}")

        logger.info(f"Downloaded {len(successful_downloads)} of {len(url_list)} PDFs")
        return successful_downloads

    def download_from_file(self, file_path):
        """
        Download PDFs from a file containing URLs, one per line.

        Args:
            file_path (str): Path to the file containing URLs

        Returns:
            list: List of successfully downloaded file paths
        """
        try:
            with open(file_path, "r") as f:
                urls = [line.strip() for line in f if line.strip()]

            logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            return self.download_from_list(urls)

        except Exception as e:
            logger.error(f"Error reading URL file {file_path}: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    downloader = PDFDownloader()

    # Example URLs (these are placeholders)
    sample_urls = [
        "https://se.jura.com/-/media/global/pdf/manuals-global/home/ENA-Micro/download_manual_jura_ena-micro1.pdf?la=sv&hash=B9A9420DF11437AE70F029B0195163A63048E7DD&em_force=true",
    ]

    downloaded_files = downloader.download_from_list(sample_urls)
    print(f"Downloaded files: {downloaded_files}")
