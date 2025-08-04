#!/usr/bin/env python3
"""
CLI for coordinate-based PDF form filling with real-time preview.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from formfill.coordinate_filler import CoordinateFiller


def load_data_from_json(json_path: str) -> dict:
    """Load form data from JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Extract collected_answers if present
        if "collected_answers" in data:
            return data["collected_answers"]
        return data
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        sys.exit(1)


def load_data_from_string(data_string: str) -> dict:
    """Parse form data from string format."""
    data = {}
    pairs = data_string.split(', ')
    
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)
            data[key.strip()] = value.strip()
    
    return data


async def main():
    parser = argparse.ArgumentParser(
        description="Coordinate-based PDF form filler with real-time preview",
        epilog="""
Examples:
  # Basic usage with JSON data
  python3 coordinate_fill_cli.py examples/sample_form.pdf -j examples/sample_answers.json
  
  # Using string data
  python3 coordinate_fill_cli.py form.pdf -s "Name: John Doe, Email: john@example.com"
  
  # Preview only (no PDF output)
  python3 coordinate_fill_cli.py form.pdf -j data.json --preview-only
  
  # Custom output paths
  python3 coordinate_fill_cli.py form.pdf -j data.json -o filled_form.pdf --preview preview.png
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('pdf_file', help='Path to PDF form to fill')
    
    # Data input options
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument('-j', '--json', help='Path to JSON file containing form data')
    data_group.add_argument('-s', '--string', help='Form data as comma-separated string')
    
    # Output options
    parser.add_argument('-o', '--output', help='Output PDF path (default: {input}_filled.pdf)')
    parser.add_argument('--preview', help='Preview image path (default: {input}_preview.png)')
    parser.add_argument('--preview-only', action='store_true', help='Generate preview only, no PDF output')
    parser.add_argument('--no-labels', action='store_true', help='Hide field labels in preview')
    
    # Interactive options
    parser.add_argument('--interactive', action='store_true', help='Interactive mode for adjusting placements')
    parser.add_argument('--show-confidence', action='store_true', help='Show confidence scores')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.pdf_file).exists():
        print(f"Error: PDF file '{args.pdf_file}' not found")
        sys.exit(1)
    
    # Load data
    if args.json:
        print(f"📄 Loading data from {args.json}")
        data = load_data_from_json(args.json)
    else:
        print("📄 Parsing string data")
        data = load_data_from_string(args.string)
    
    print(f"📋 Loaded {len(data)} data fields:")
    for key, value in data.items():
        print(f"  • {key}: {value}")
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   Please set your API key: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Initialize filler
    print("🚀 Initializing coordinate filler...")
    filler = CoordinateFiller(api_key)
    
    # Analyze form
    print("🔍 Analyzing form fields with Claude...")
    try:
        placements = await filler.analyze_form_fields(args.pdf_file, data)
    except Exception as e:
        print(f"❌ Error analyzing form: {e}")
        sys.exit(1)
    
    if not placements:
        print("⚠️  No form fields detected. Please check your PDF and try again.")
        sys.exit(1)
    
    print(f"📍 Found {len(placements)} field placements:")
    for i, p in enumerate(placements):
        confidence_str = f" [confidence: {p.confidence:.2f}]" if args.show_confidence else ""
        print(f"  {i+1:2d}. {p.field_name:20s}: '{p.text}' at ({p.x:3d}, {p.y:3d}){confidence_str}")
    
    # Interactive adjustment mode
    if args.interactive:
        print("\n🔧 Interactive mode - You can adjust placements:")
        print("Commands:")
        print("  adjust <index> <x> <y> - Move placement")
        print("  remove <index>         - Remove placement")
        print("  add <name> <text> <x> <y> - Add placement")
        print("  preview                - Show current preview")
        print("  done                   - Finish and save")
        
        while True:
            try:
                cmd = input("\n> ").strip().split()
                if not cmd:
                    continue
                    
                if cmd[0] == "done":
                    break
                elif cmd[0] == "adjust" and len(cmd) >= 4:
                    idx, x, y = int(cmd[1]) - 1, int(cmd[2]), int(cmd[3])
                    filler.adjust_placement(idx, x, y)
                    print(f"✅ Adjusted placement {idx + 1}")
                elif cmd[0] == "remove" and len(cmd) >= 2:
                    idx = int(cmd[1]) - 1
                    filler.remove_placement(idx)
                    print(f"✅ Removed placement {idx + 1}")
                elif cmd[0] == "add" and len(cmd) >= 5:
                    name, text, x, y = cmd[1], cmd[2], int(cmd[3]), int(cmd[4])
                    filler.add_placement(name, text, x, y)
                    print(f"✅ Added placement: {name}")
                elif cmd[0] == "preview":
                    preview_path = args.preview or f"{Path(args.pdf_file).stem}_preview.png"
                    filler.save_preview(preview_path, not args.no_labels)
                    print(f"👁️  Preview saved: {preview_path}")
                else:
                    print("❌ Invalid command. Use: adjust/remove/add/preview/done")
            except (ValueError, IndexError) as e:
                print(f"❌ Error: {e}")
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                sys.exit(0)
    
    # Generate preview
    preview_path = args.preview or f"{Path(args.pdf_file).stem}_preview.png"
    print(f"🖼️  Creating preview: {preview_path}")
    filler.save_preview(preview_path, not args.no_labels)
    print(f"   ✅ Preview saved! Open '{preview_path}' to verify placements")
    
    # Generate filled PDF (unless preview-only mode)
    if not args.preview_only:
        output_path = args.output or f"{Path(args.pdf_file).stem}_filled.pdf"
        print(f"📄 Writing filled PDF: {output_path}")
        try:
            result_path = filler.write_to_pdf(output_path)
            print(f"   ✅ Filled PDF saved: {result_path}")
        except Exception as e:
            print(f"❌ Error writing PDF: {e}")
            sys.exit(1)
    
    print("\n🎉 Process completed successfully!")
    print(f"📋 Summary:")
    print(f"   • Fields processed: {len(placements)}")
    print(f"   • Preview: {preview_path}")
    if not args.preview_only:
        print(f"   • Filled PDF: {output_path}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        sys.exit(0)