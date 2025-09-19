---
description: Repository Information Overview
alwaysApply: true
---

# Anclora AI RAG Information

## Summary

Anclora AI RAG is a Retrieval-Augmented Generation system that allows users to upload documents and make queries against them using open-source language models like Llama3-7b and Phi3-4b. The application provides a multilingual interface (Spanish, English, French, German) and uses Docker for containerization.

## Structure

- **app/**: Main application code including Streamlit UI, document processing, and RAG implementation
- **docs/**: Documentation files for the project
- **.vscode/**: VS Code configuration
- **docker-compose.yml**: Docker configuration for GPU-enabled setup (Llama3)
- **docker-compose_sin_gpu.yml**: Docker configuration for CPU-only setup (Phi3)

## Language & Runtime

**Language**: Python 3.11
**Framework**: Streamlit
**Build System**: Docker
**Package Manager**: pip

## Dependencies

**Main Dependencies**:

- langchain (0.1.16)
- langchain-community (0.0.34)
- chromadb (0.4.7)
- streamlit
- sentence_transformers
- PyMuPDF (1.23.5)
- ollama (via Docker)

**External Services**:

- ChromaDB (vector database)
- Ollama (LLM service)

## Build & Installation

```bash
# With GPU support (Llama3)
docker-compose up

# Without GPU (Phi3)
# Rename docker-compose_sin_gpu.yml to docker-compose.yml first
docker-compose up
```

## Docker

**Dockerfile**: app/Dockerfile
**Images**:

- ollama/ollama:latest (LLM service)
- chromadb/chroma:0.5.1.dev111 (Vector database)
- nvidia/cuda:12.3.1-base-ubuntu20.04 (GPU support)
- Custom UI image built from ./app

**Configuration**:

- GPU passthrough for Llama3 model
- CPU-only configuration available for Phi3 model
- Persistent volume for ChromaDB
- Environment variables for model selection and embedding configuration

## Main Files

**Entry Point**: app/Inicio.py
**Key Modules**:

- app/common/langchain_module.py: RAG implementation
- app/common/ingest_file.py: Document processing
- app/common/assistant_prompt.py: LLM prompt template
- app/pages/Archivos.py: File management interface

## Usage

The application runs on <http://localhost:8080> and provides:

- Chat interface for querying documents
- File upload interface for adding documents to the knowledge base
- Language selection for the UI
- Document management (view and delete)
