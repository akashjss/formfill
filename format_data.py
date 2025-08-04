#!/usr/bin/env python3
"""
Data formatter script for FormFill application.

This script extracts data from a JSON file and formats it for use with the FormFill CLI.
It can output either a formatted string or CSV format.
"""

import json
import csv
import argparse
import sys
from pathlib import Path


def load_json_data(json_file_path):
    """Load JSON data from file."""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{json_file_path}': {e}")
        sys.exit(1)


def extract_answers(data):
    """Extract collected_answers from the JSON data."""
    if "collected_answers" not in data:
        print("Error: 'collected_answers' key not found in JSON data.")
        sys.exit(1)
    return data["collected_answers"]


def format_as_string(answers):
    """Format answers as a comma-separated string for CLI usage."""
    formatted_pairs = []
    for key, value in answers.items():
        # Clean up the key and value for better readability
        clean_key = key.replace("_", " ").title()
        formatted_pairs.append(f"{clean_key}: {value}")
    
    return ", ".join(formatted_pairs)


def format_as_csv(answers, output_file):
    """Format answers as CSV file."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Field', 'Value'])
        
        # Write data
        for key, value in answers.items():
            clean_key = key.replace("_", " ").title()
            writer.writerow([clean_key, value])
    
    print(f"CSV file created: {output_file}")


def print_usage_examples(json_file, form_file):
    """Print usage examples for the FormFill CLI."""
    print("\n" + "="*60)
    print("🚀 USAGE EXAMPLES:")
    print("="*60)
    
    print(f"\n1. Using string format (recommended for testing):")
    print(f"   python3 format_data.py {json_file} --string")
    
    print(f"\n2. Creating CSV file:")
    print(f"   python3 format_data.py {json_file} --csv output.csv")
    
    print(f"\n3. Running FormFill with string data:")
    print(f"   python3 -m formfill.cli {form_file} -s \"$(python3 format_data.py {json_file} --string)\"")
    
    print(f"\n4. Running FormFill with CSV file:")
    print(f"   python3 format_data.py {json_file} --csv data.csv")
    print(f"   python3 -m formfill.cli {form_file} -f data.csv")
    
    print(f"\n5. With verbose logging:")
    print(f"   python3 -m formfill.cli {form_file} -s \"$(python3 format_data.py {json_file} --string)\" -v")


def main():
    parser = argparse.ArgumentParser(
        description="Format JSON answers data for FormFill application",
        epilog="Example: python3 format_data.py examples/sample_answers.json --string"
    )
    
    parser.add_argument('json_file', help='Path to JSON file containing answers')
    parser.add_argument('--string', action='store_true', help='Output as formatted string')
    parser.add_argument('--csv', metavar='OUTPUT_FILE', help='Output as CSV file')
    parser.add_argument('--examples', action='store_true', help='Show usage examples')
    
    args = parser.parse_args()
    
    # Load and extract data
    data = load_json_data(args.json_file)
    answers = extract_answers(data)
    
    if args.string:
        # Output formatted string
        formatted_string = format_as_string(answers)
        print(formatted_string)
    
    elif args.csv:
        # Output CSV file
        format_as_csv(answers, args.csv)
    
    elif args.examples:
        # Show usage examples
        json_path = Path(args.json_file)
        form_file = json_path.parent / "sample_form.pdf"
        print_usage_examples(args.json_file, form_file)
    
    else:
        # Default: show formatted data and examples
        print("📋 EXTRACTED DATA:")
        print("-" * 40)
        for key, value in answers.items():
            clean_key = key.replace("_", " ").title()
            print(f"{clean_key:30}: {value}")
        
        # Show usage examples
        json_path = Path(args.json_file)
        form_file = json_path.parent / "sample_form.pdf"
        print_usage_examples(args.json_file, form_file)


if __name__ == "__main__":
    main()