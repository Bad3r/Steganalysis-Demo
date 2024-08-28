#!/usr/bin/env python3
# extract_hidden_files.py

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define common file signatures (headers) to identify file types and their footers (if applicable)
FILE_SIGNATURES = {
    b'\x50\x4B\x03\x04': ('zip', b'PK\x05\x06'),   # ZIP file with footer PK\x05\x06
    b'\x25\x50\x44\x46': ('pdf', b'\x25\x25\x45\x4F\x46'),   # PDF file with EOF %%EOF
    b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': ('png', b'\x49\x45\x4E\x44\xAE\x42\x60\x82'),  # PNG file with IEND footer
    b'\xFF\xD8\xFF': ('jpg', b'\xFF\xD9'),       # JPEG file with footer FF D9
    b'\x47\x49\x46\x38\x37\x61': ('gif', None),  # GIF file (version 87a) - no standard footer
    b'\x47\x49\x46\x38\x39\x61': ('gif', None),  # GIF file (version 89a) - no standard footer
    b'\x49\x49\x2A\x00': ('tiff', None),  # TIFF file (little-endian) - no standard footer
    b'\x4D\x4D\x00\x2A': ('tiff', None),  # TIFF file (big-endian) - no standard footer
    b'\xEF\xBB\xBF': ('txt', None),       # UTF-8 encoded text file with BOM - no standard footer
    b'\xFF\xFE': ('txt', None),           # UTF-16 LE text file - no standard footer
    b'\xFE\xFF': ('txt', None),           # UTF-16 BE text file - no standard footer
    b'\x00\x00\xFE\xFF': ('txt', None),   # UTF-32 BE text file - no standard footer
    b'\xFF\xFE\x00\x00': ('txt', None),   # UTF-32 LE text file - no standard footer
}

def find_file_signatures(data: bytes) -> list:
    """
    Find all file signatures in the given binary data.
    Parameters:
        data (bytes): The binary data to search for file signatures.
    Returns:
        list: A list of tuples containing the file signature, offset, file extension, and footer.
    """
    signatures = []
    for signature, (extension, footer) in FILE_SIGNATURES.items():
        offset = data.find(signature)
        while offset != -1:
            signatures.append((signature, offset, extension, footer))
            offset = data.find(signature, offset + 1)
    signatures.sort(key=lambda x: x[1])
    return signatures

def extract_filename(data: bytes, start: int, extension: str) -> str:
    """
    Attempt to extract the filename from the binary data near the signature.
    Parameters:
        data (bytes): The binary data containing the file.
        start (int): The offset where the file signature is found.
        extension (str): The file extension determined by the signature.
    Returns:
        str: The extracted filename or a default name based on the extension.
    """
    possible_filename = data[start:start+100].decode('utf-8', errors='ignore')
    for part in possible_filename.split('\x00'):
        if len(part) > 1 and '.' in part and part.split('.')[-1] == extension:
            return part.strip()
    return f'file.{extension}'

def extract_files_from_image(image_path: Path, output_directory: Path) -> None:
    """
    Extract hidden files from an image by processing its hex data.
    Parameters:
        image_path (Path): The path to the image with hidden files.
        output_directory (Path): The directory to save the extracted files.
    Returns:
        None
    """
    with open(image_path, 'rb') as img_file:
        data = img_file.read()

    signatures = find_file_signatures(data)

    if not signatures:
        logging.info("No recognizable file signatures found in the image.")
        return

    for i, (signature, offset, extension, footer) in enumerate(signatures):
        start = offset
        if footer:
            end = data.find(footer, start) + len(footer)
        else:
            end = signatures[i + 1][1] if i + 1 < len(signatures) else len(data)

        file_data = data[start:end]

        filename = extract_filename(file_data, 0, extension)
        output_file = output_directory / f"extracted_{filename}"

        with open(output_file, 'wb') as f:
            f.write(file_data)
        logging.info(f"Extracted file saved as {output_file} (size: {len(file_data)} bytes)")

def main() -> None:
    """
    The main function that orchestrates the extraction of hidden files from an image.
    This function:
    1. Validates input parameters.
    2. Extracts hidden files from the image by searching for file signatures.
    3. Saves the extracted files to the specified output directory.
    Command-Line Usage:
        python extract_hidden_files.py <image_with_hidden_files> [output_directory]
    Returns:
        None
    Exits:
        1: If there are insufficient command-line arguments.
        1: If any file-related errors occur during execution.
    """
    if len(sys.argv) < 2:
        logging.error("Usage: python extract_hidden_files.py <image_with_hidden_files> [output_directory]")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    output_directory = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()

    if not image_path.exists() or not image_path.is_file():
        logging.error(f"Image file '{image_path}' not found.")
        sys.exit(1)

    if not output_directory.exists():
        output_directory.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created output directory '{output_directory}'.")

    try:
        extract_files_from_image(image_path, output_directory)
        logging.info("File extraction completed successfully.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
