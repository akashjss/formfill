#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image

from .fill import fill_form


# Set up logger
logger = logging.getLogger('formfill')

def setup_logging(verbose: bool):
    """Configure logging based on verbosity level"""
    # Configure log formatting
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Set up the logger
    logger.addHandler(console_handler)
    
    # Set log level based on verbose flag
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def images_to_pdf(images: list[Image.Image], output_path: str) -> None:
    images[0].save(
        output_path,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=images[1:]
    )


async def main():
    os.environ["HEIGHT"] = "768"
    os.environ["WIDTH"] = "1024"
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fill PDF forms with provided data')
    parser.add_argument('form', help='Path to the PDF form')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='Path to CSV file containing form data')
    group.add_argument('-s', '--string', help='Direct string input for form data')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose debug logging')    

    args = parser.parse_args()

    setup_logging(args.verbose)
    
    try:
        # Verify input PDF exists
        if not os.path.exists(args.form):
            raise FileNotFoundError(f"Form PDF not found: {args.form}")
        
        # Get input data
        if args.string:
            data = args.string
        else:
            with open(args.file) as f:
                data = f.read()
        
        # Convert PDF to images
        images = convert_from_path(args.form)
        
        # Process each page
        processed_images = []
        for img in images:
            filled_img = await fill_form(img, data)
            
            processed_images.append(filled_img)
        
        # Generate output filename
        input_path = Path(args.form)
        output_path = f"{input_path.stem}_filled.pdf"
        
        # Convert processed images back to PDF
        images_to_pdf(processed_images, str(output_path))
        
        print(f"Form successfully filled and saved as: {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


def run_cli():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        exit(1)


if __name__ == "__main__":
    run_cli()
