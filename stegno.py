#!/usr/bin/env python3
# stegno.py

import sys
import logging
from zipfile import ZipFile
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the separator and metadata structure
SEPARATOR = b'\r\n\r\n'
FILENAME_SEPARATOR = b'\0'
LENGTH_FIELD_SIZE = 10  # 10 bytes for file length

def human_readable_size(size: int) -> str:
    """Convert a file size in bytes to a human-readable string using binary prefixes."""
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024:
            return f"{size} {unit}"
        size //= 1024
    return f"{size} EiB"

def validate_inputs(image_path: Path, files_to_hide: list[Path]) -> None:
    """Validate the input image and files to hide."""
    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"Image file '{image_path}' not found.")
    for file_path in files_to_hide:
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File '{file_path}' not found.")

def collect_files_from_directory(directory: Path) -> list[Path]:
    """Collect all files from a directory."""
    return [file for file in directory.rglob('*') if file.is_file()]

def create_zip_with_files(zip_name: str, files: list[Path]) -> None:
    """Create a ZIP archive containing the files to be hidden."""
    with ZipFile(zip_name, 'w') as zipf:
        for file_path in files:
            arcname = file_path.relative_to(files[0].parent)  # Preserve directory structure
            zipf.write(file_path, arcname=arcname)

def concatenate_image_and_files(image_path: Path, zip_path: str, files: list[Path], output_image_path: str) -> None:
    """Concatenate the image with the ZIP file, adding metadata for non-ZIP files."""
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()

    with open(output_image_path, 'wb') as output_file:
        output_file.write(image_data)
        if zip_path:
            with open(zip_path, 'rb') as zip_file:
                output_file.write(zip_file.read())

        for file_path in files:
            file_size = file_path.stat().st_size
            file_name = file_path.name.encode('utf-8')
            # Write metadata: file length, file name, separator
            output_file.write(f"{file_size:<{LENGTH_FIELD_SIZE}}".encode('utf-8') + file_name + FILENAME_SEPARATOR)
            # Write file content
            with open(file_path, 'rb') as f:
                output_file.write(f.read())
            output_file.write(SEPARATOR)

def log_file_sizes(image_file: Path, files_to_hide: list[Path]) -> int:
    """Log the sizes of the image file and the files to hide."""
    image_size = image_file.stat().st_size
    logging.info(f"Original image size: {human_readable_size(image_size)}")
    total_files_size = 0
    for file_path in files_to_hide:
        file_size = file_path.stat().st_size
        total_files_size += file_size
        logging.info(f"File '{file_path}' size: {human_readable_size(file_size)}")
    logging.info(f"Total size of files to hide: {human_readable_size(total_files_size)}")
    return total_files_size

def log_final_image_size(output_image: Path) -> None:
    """Log the final size of the image after concatenation."""
    final_image_size = output_image.stat().st_size
    logging.info(f"New image size: {human_readable_size(final_image_size)}")

def main() -> None:
    """Main function for hiding files inside an image."""
    if len(sys.argv) < 3:
        logging.error("Usage: python stegno.py <image_file> <file_to_hide1> [file_to_hide2 ...]")
        logging.error("       or python stegno.py <image_file> <directory>")
        sys.exit(1)

    image_file = Path(sys.argv[1])
    second_arg = Path(sys.argv[2])

    try:
        if second_arg.is_dir():
            files_to_hide = collect_files_from_directory(second_arg)
        else:
            files_to_hide = [second_arg] + [Path(file) for file in sys.argv[3:]]

        validate_inputs(image_file, files_to_hide)

        log_file_sizes(image_file, files_to_hide)

        # Create a ZIP file if more than one file is being hidden
        zip_name = None
        if len(files_to_hide) > 1:
            zip_name = f"hidden_files_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
            create_zip_with_files(zip_name, files_to_hide)

        # Otherwise, use the metadata approach
        output_image = image_file.stem + "_with_hidden_files" + image_file.suffix
        concatenate_image_and_files(image_file, zip_name, files_to_hide if not zip_name else [], output_image)

        if zip_name:
            Path(zip_name).unlink()  # Clean up the temporary zip file

        log_final_image_size(Path(output_image))

        logging.info(f"Files hidden inside '{output_image}'.")
        logging.info(f"Use a zip tool to extract the hidden files from '{output_image}' if they are in ZIP format.")

    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)
    except OSError as e:
        logging.error(f"File operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
