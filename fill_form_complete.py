#!/usr/bin/env python3
"""
Complete form filling workflow that combines data formatting with coordinate-based filling.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


def format_json_data(json_file):
    """Format JSON data using the existing format_data.py script."""
    try:
        result = subprocess.run([
            'python3', 'format_data.py', json_file, '--string'
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error formatting data: {e}")
        return None


def run_coordinate_filler(pdf_file, json_file, preview_only=False, interactive=False):
    """Run the coordinate-based filler."""
    cmd = ['python3', 'coordinate_fill_cli.py', pdf_file, '-j', json_file]
    
    if preview_only:
        cmd.append('--preview-only')
    if interactive:
        cmd.append('--interactive')
    
    try:
        result = subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running coordinate filler: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Complete PDF form filling workflow",
        epilog="""
Examples:
  # Quick preview
  python3 fill_form_complete.py examples/sample_form.pdf examples/sample_answers.json --preview
  
  # Full filling process
  python3 fill_form_complete.py examples/sample_form.pdf examples/sample_answers.json
  
  # Interactive mode for fine-tuning
  python3 fill_form_complete.py examples/sample_form.pdf examples/sample_answers.json --interactive
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('pdf_file', help='Path to PDF form to fill')
    parser.add_argument('json_file', help='Path to JSON file with form data')
    parser.add_argument('--preview', action='store_true', help='Generate preview only')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode for adjustments')
    parser.add_argument('--method', choices=['coordinate', 'computer_use'], default='coordinate',
                       help='Filling method to use (default: coordinate)')
    
    args = parser.parse_args()
    
    # Validate files
    if not Path(args.pdf_file).exists():
        print(f"❌ Error: PDF file '{args.pdf_file}' not found")
        sys.exit(1)
        
    if not Path(args.json_file).exists():
        print(f"❌ Error: JSON file '{args.json_file}' not found")
        sys.exit(1)
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    print("🚀 Starting complete form filling workflow...")
    print(f"📄 PDF: {args.pdf_file}")
    print(f"📋 Data: {args.json_file}")
    print(f"🔧 Method: {args.method}")
    
    if args.method == 'coordinate':
        print("\n🎯 Using coordinate-based filling (recommended for non-fillable PDFs)")
        success = run_coordinate_filler(args.pdf_file, args.json_file, args.preview, args.interactive)
        
        if success:
            print("\n✅ Coordinate-based filling completed successfully!")
            if not args.preview:
                output_name = Path(args.pdf_file).stem + "_filled.pdf"
                print(f"📄 Filled PDF: {output_name}")
            preview_name = Path(args.pdf_file).stem + "_preview.png"
            print(f"🖼️  Preview: {preview_name}")
        else:
            print("\n❌ Coordinate-based filling failed")
            
    elif args.method == 'computer_use':
        print("\n🖱️  Using computer use method (for fillable PDFs)")
        
        # Format the data
        print("📝 Formatting data...")
        formatted_data = format_json_data(args.json_file)
        if not formatted_data:
            print("❌ Failed to format data")
            sys.exit(1)
            
        print(f"📋 Formatted data: {formatted_data[:100]}...")
        
        # Run FormFill
        print("🔄 Running FormFill...")
        try:
            cmd = ['python3', '-m', 'formfill.cli', args.pdf_file, '-s', formatted_data]
            if args.preview:
                cmd.append('-v')  # Verbose mode for preview
                
            subprocess.run(cmd, check=True)
            print("✅ Computer use filling completed successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ FormFill failed: {e}")
            sys.exit(1)
    
    print("\n🎉 Workflow completed!")


if __name__ == "__main__":
    main()