#!/usr/bin/env python3
"""
Script to fix text normalization issues in the project.

This script scans all text files (markdown, Python, etc.) and applies NFC normalization
to fix combining character issues that can cause problems with text processing and search.
"""

import os
import sys
import unicodedata
from pathlib import Path
from typing import List, Set, Optional

# File extensions to check for normalization issues
TEXT_EXTENSIONS = {'.md', '.py', '.txt', '.yml', '.yaml', '.json', '.toml', '.cfg', '.ini', '.sh', '.bat'}

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    '.git',
    '__pycache__',
    '.pytest_cache',
    'node_modules',
    '.vscode',
    'venv',
    'env',
    'build',
    'dist'
}

def normalize_to_nfc(text: str) -> str:
    """Return the NFC-normalized version of text."""
    if text is None:
        return ""
    return unicodedata.normalize("NFC", text)

def has_normalization_issues(text: str) -> bool:
    """Check if text has combining character normalization issues."""
    # Check if text contains combining characters that could be normalized
    nfc_normalized = normalize_to_nfc(text)
    return text != nfc_normalized

def fix_file_normalization(file_path: Path) -> bool:
    """Fix normalization issues in a single file."""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file has normalization issues
        if not has_normalization_issues(content):
            return False

        # Apply NFC normalization
        normalized_content = normalize_to_nfc(content)

        # Write back the normalized content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(normalized_content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def scan_and_fix_files(root_dir: Path, extensions: Optional[Set[str]] = None) -> dict:
    """Scan all files and fix normalization issues."""
    if extensions is None:
        extensions = TEXT_EXTENSIONS

    stats = {
        'files_checked': 0,
        'files_fixed': 0,
        'errors': 0
    }

    print(f"Scanning for normalization issues in {root_dir}...")

    for file_path in root_dir.rglob('*'):
        # Skip directories
        if file_path.is_dir():
            if file_path.name in EXCLUDE_DIRS:
                file_path = Path(*file_path.parts[:-1])  # Go up one level to continue
                continue
            continue

        # Check file extension
        if file_path.suffix.lower() not in extensions:
            continue

        stats['files_checked'] += 1

        # Try to fix the file
        try:
            if fix_file_normalization(file_path):
                stats['files_fixed'] += 1
                print(f"Fixed: {file_path}")
        except Exception as e:
            stats['errors'] += 1
            print(f"Error with {file_path}: {e}")

    return stats

def main():
    """Main function to run the normalization fix."""
    # Get the project root directory
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    else:
        root_dir = Path.cwd()

    print("Text Normalization Fixer")
    print("=" * 50)
    print(f"Root directory: {root_dir}")
    print(f"File extensions: {', '.join(sorted(TEXT_EXTENSIONS))}")
    print()

    # Scan and fix files
    stats = scan_and_fix_files(root_dir)

    print("\n" + "=" * 50)
    print("Results Summary:")
    print(f"Files checked: {stats['files_checked']}")
    print(f"Files fixed: {stats['files_fixed']}")
    print(f"Errors: {stats['errors']}")

    if stats['files_fixed'] > 0:
        print("\nNormalization issues have been fixed!")
        print("Note: The text normalization system in the app will now work correctly with these files.")
    else:
        print("\nNo normalization issues found!")

    return 0 if stats['errors'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())