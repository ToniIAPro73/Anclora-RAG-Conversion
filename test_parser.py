#!/usr/bin/env python3
"""Test script to verify the markdown parser works with the new format."""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ingestion.markdown_source_parser import MarkdownSourceParser

async def test_parser():
    parser = MarkdownSourceParser()

    # Read the test file with proper encoding handling
    try:
        # Try to detect the encoding using chardet
        import chardet

        # Read a sample of the file to detect encoding
        with open('docs/fuentes_originales.md', 'rb') as f:
            raw_data = f.read()
            detection_result = chardet.detect(raw_data)
            detected_encoding = detection_result.get('encoding', 'utf-8')
            confidence = detection_result.get('confidence', 0)

        print(f"Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")

        # Try the detected encoding first
        encodings_to_try = [detected_encoding, 'utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']

        for encoding in encodings_to_try:
            try:
                with open('docs/fuentes_originales.md', 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Successfully read file with encoding: {encoding}")

                # Check if the content contains the corrupted characters
                if '�' not in content:
                    print(f"Clean content found with encoding: {encoding}")
                    break
                else:
                    print(f"Content contains corrupted characters with encoding: {encoding}")
                    continue

            except UnicodeDecodeError:
                print(f"Failed to read with encoding: {encoding}")
                continue
            except FileNotFoundError:
                print("Error: File 'docs/fuentes_originales.md' not found")
                return 0
        else:
            print("Could not read file cleanly with any encoding")
            # Use the first successful read even if it has corrupted characters
            with open('docs/fuentes_originales.md', 'r', encoding='utf-8') as f:
                content = f.read()

    except ImportError:
        # chardet not available, try common encodings
        print("chardet not available, trying common encodings...")
        encodings_to_try = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']

        for encoding in encodings_to_try:
            try:
                with open('docs/fuentes_originales.md', 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Successfully read file with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                print(f"Failed to read with encoding: {encoding}")
                continue
            except FileNotFoundError:
                print("Error: File 'docs/fuentes_originales.md' not found")
                return 0
        else:
            print("Could not read file with any encoding")
            return 0

    print(f"File size: {len(content)} characters")

    # Test validation
    validation = await parser.validate_source_format(content)
    print(f"Validation result: {validation}")

    # Test parsing
    sources = await parser.parse_sources(content)
    print(f"Parsed {len(sources)} sources")

    if sources:
        print("\nFirst source:")
        for key, value in sources[0].items():
            print(f"  {key}: {value[:100]}..." if len(str(value)) > 100 else f"  {key}: {value}")

    return len(sources)

if __name__ == "__main__":
    result = asyncio.run(test_parser())
    print(f"\nTotal sources detected: {result}")