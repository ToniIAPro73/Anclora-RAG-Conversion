"""Agent focused on processing compressed archive files."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, List, Mapping, MutableMapping, Sequence

import sys
import os

# Add the app directory to the path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(current_dir))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from agents.base import AgentResponse, AgentTask, BaseAgent
from agents.archive_agent.ingestor import ARCHIVE_COLLECTION
from common.observability import record_agent_invocation


_ContextItem = Mapping[str, Any]
_Retriever = Callable[[str, int], Sequence[_ContextItem]]
_CollectionResolver = Callable[[str], Any]


@dataclass(frozen=True)
class ArchiveAgentConfig:
    """Configuration options for :class:`ArchiveAgent`."""

    collection_name: str = ARCHIVE_COLLECTION
    max_results: int = 5


class ArchiveAgent(BaseAgent):
    """Retrieve content from compressed archive files."""

    SUPPORTED_TASKS = {"archive_processing", "document_extraction"}

    def __init__(
        self,
        config: ArchiveAgentConfig | None = None,
        retriever: _Retriever | None = None,
        collection_resolver: _CollectionResolver | None = None,
    ) -> None:
        super().__init__(name="archive_agent")
        self._config = config or ArchiveAgentConfig()
        self._retriever = retriever
        if retriever is None:
            from common.chroma_db_settings import Chroma
            from common.embeddings_manager import get_embeddings

            def default_retriever(query: str, max_results: int) -> Sequence[_ContextItem]:
                embeddings = get_embeddings("archives")
                collection = collection_resolver(self._config.collection_name) if collection_resolver else None
                
                if collection is None:
                    db = Chroma(
                        collection_name=self._config.collection_name,
                        embedding_function=embeddings,
                    )
                    collection = db._collection

                results = collection.query(
                    query_texts=[query],
                    n_results=max_results,
                    include=["documents", "metadatas", "distances"]
                )

                items = []
                if results["documents"] and results["documents"][0]:
                    for doc, metadata, distance in zip(
                        results["documents"][0],
                        results["metadatas"][0] or [{}] * len(results["documents"][0]),
                        results["distances"][0] or [0.0] * len(results["documents"][0])
                    ):
                        items.append({
                            "content": doc,
                            "metadata": metadata,
                            "distance": distance
                        })

                return items

            self._retriever = default_retriever

    def process_task(self, task: AgentTask) -> AgentResponse:
        """Process archive-related tasks."""
        
        start_time = time.time()
        
        try:
            # Extract query from task
            query = task.query or ""
            
            # Retrieve relevant archive content
            context_items = self._retriever(query, self._config.max_results)
            
            # Format response
            if not context_items:
                content = "No se encontraron documentos relevantes en los archivos comprimidos."
                sources = []
            else:
                # Build response from archive content
                content_parts = []
                sources = []
                
                for item in context_items:
                    doc_content = item.get("content", "")
                    metadata = item.get("metadata", {})
                    
                    # Extract source information
                    archive_path = metadata.get("archive_path", "")
                    source_file = metadata.get("source", "")
                    parser_used = metadata.get("parser", "unknown")
                    
                    if archive_path:
                        source_info = f"{archive_path} (procesado con {parser_used})"
                        sources.append(source_info)
                        
                        # Add content with source context
                        content_parts.append(f"**Archivo: {archive_path}**\n{doc_content}")
                
                content = "\n\n---\n\n".join(content_parts)
            
            # Record metrics
            processing_time = time.time() - start_time
            record_agent_invocation(
                agent_name=self.name,
                task_type=task.task_type,
                processing_time=processing_time,
                success=True
            )
            
            return AgentResponse(
                agent_name=self.name,
                content=content,
                sources=sources,
                metadata={
                    "collection": self._config.collection_name,
                    "results_count": len(context_items),
                    "processing_time": processing_time
                }
            )
            
        except Exception as e:
            # Record error metrics
            processing_time = time.time() - start_time
            record_agent_invocation(
                agent_name=self.name,
                task_type=task.task_type,
                processing_time=processing_time,
                success=False
            )
            
            return AgentResponse(
                agent_name=self.name,
                content=f"Error procesando archivos comprimidos: {str(e)}",
                sources=[],
                metadata={
                    "error": str(e),
                    "processing_time": processing_time
                }
            )

    def get_supported_tasks(self) -> set[str]:
        """Return the set of supported task types."""
        return self.SUPPORTED_TASKS
