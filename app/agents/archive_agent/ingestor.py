"""Ingestion helpers for compressed archive files."""
from __future__ import annotations

import os
import tempfile
import zipfile
from typing import List, Dict, Any
from pathlib import Path

# Provide fallback for environments without llama-parse
try:
    from llama_parse import LlamaParse
    LLAMA_PARSE_AVAILABLE = True
except ImportError:
    LLAMA_PARSE_AVAILABLE = False
    LlamaParse = None

try:
    from langchain_community.document_loaders import TextLoader
except ImportError:
    from common.text_normalization import Document

    class TextLoader:
        def __init__(self, file_path: str, encoding: str = "utf8", **_: object) -> None:
            self.file_path = file_path
            self.encoding = encoding

        def load(self):
            with open(self.file_path, "r", encoding=self.encoding) as handle:
                return [Document(page_content=handle.read(), metadata={"source": self.file_path})]

from ..base import BaseFileIngestor


class ZipFileLoader:
    """Custom loader for ZIP files using LlamaParse or fallback extraction."""
    
    def __init__(self, file_path: str, **kwargs):
        self.file_path = file_path
        self.kwargs = kwargs
        
    def load(self) -> List[Any]:
        """Load and process ZIP file contents."""
        documents = []
        
        try:
            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                # Create temporary directory for extraction
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Extract all files
                    zip_ref.extractall(temp_dir)
                    
                    # Process each extracted file
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, temp_dir)
                            
                            try:
                                # Try to process with LlamaParse if available
                                if LLAMA_PARSE_AVAILABLE and self._should_use_llama_parse(file):
                                    docs = self._process_with_llama_parse(file_path, relative_path)
                                else:
                                    docs = self._process_with_text_loader(file_path, relative_path)
                                
                                documents.extend(docs)
                                
                            except Exception as e:
                                # Create error document for failed files
                                error_doc = self._create_error_document(relative_path, str(e))
                                documents.append(error_doc)
                                
        except Exception as e:
            # Create error document for ZIP processing failure
            error_doc = self._create_error_document(self.file_path, f"ZIP processing failed: {str(e)}")
            documents.append(error_doc)
            
        return documents
    
    def _should_use_llama_parse(self, filename: str) -> bool:
        """Determine if file should be processed with LlamaParse."""
        # Use LlamaParse for complex document formats
        complex_formats = {'.pdf', '.docx', '.pptx', '.xlsx'}
        file_ext = Path(filename).suffix.lower()
        return file_ext in complex_formats
    
    def _process_with_llama_parse(self, file_path: str, relative_path: str) -> List[Any]:
        """Process file using LlamaParse."""
        try:
            # Initialize LlamaParse
            parser = LlamaParse(
                api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
                result_type="text",
                verbose=True
            )
            
            # Parse the document
            documents = parser.load_data(file_path)
            
            # Convert to expected format
            result_docs = []
            for i, doc in enumerate(documents):
                from common.text_normalization import Document
                result_doc = Document(
                    page_content=doc.text,
                    metadata={
                        "source": file_path,
                        "archive_path": relative_path,
                        "page": i,
                        "parser": "llama_parse"
                    }
                )
                result_docs.append(result_doc)
                
            return result_docs
            
        except Exception as e:
            # Fallback to text loader
            return self._process_with_text_loader(file_path, relative_path)
    
    def _process_with_text_loader(self, file_path: str, relative_path: str) -> List[Any]:
        """Process file using standard text loader."""
        try:
            # Determine if file is text-based
            if self._is_text_file(file_path):
                loader = TextLoader(file_path, encoding="utf8")
                docs = loader.load()
                
                # Update metadata
                for doc in docs:
                    doc.metadata.update({
                        "archive_path": relative_path,
                        "parser": "text_loader"
                    })
                
                return docs
            else:
                # Skip binary files or create placeholder
                from common.text_normalization import Document
                return [Document(
                    page_content=f"Binary file: {relative_path}",
                    metadata={
                        "source": file_path,
                        "archive_path": relative_path,
                        "file_type": "binary",
                        "parser": "skipped"
                    }
                )]
                
        except Exception as e:
            return [self._create_error_document(relative_path, str(e))]
    
    def _is_text_file(self, file_path: str) -> bool:
        """Check if file is text-based."""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs',
            '.go', '.rb', '.rs', '.php', '.sql', '.html', '.css', '.json',
            '.xml', '.yaml', '.yml', '.ini', '.cfg', '.conf', '.log'
        }
        
        file_ext = Path(file_path).suffix.lower()
        return file_ext in text_extensions
    
    def _create_error_document(self, path: str, error: str) -> Any:
        """Create error document for failed processing."""
        from common.text_normalization import Document
        return Document(
            page_content=f"Error processing {path}: {error}",
            metadata={
                "source": path,
                "error": error,
                "parser": "error"
            }
        )


ARCHIVE_LOADERS = {
    ".zip": (ZipFileLoader, {}),
}

ARCHIVE_COLLECTION = "archive_documents"


def create_archive_ingestor() -> BaseFileIngestor:
    """Factory for the archive ingestor."""
    return BaseFileIngestor(
        domain="archives",
        collection_name=ARCHIVE_COLLECTION,
        loader_mapping=ARCHIVE_LOADERS,
    )


ArchiveIngestor = create_archive_ingestor()

__all__ = [
    "ARCHIVE_COLLECTION",
    "ArchiveIngestor", 
    "ZipFileLoader",
    "create_archive_ingestor",
]
