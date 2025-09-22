"""Callbacks para que el auto-optimizador controle componentes del pipeline RAG."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import os
import json

logger = logging.getLogger(__name__)


class RAGPipelineCallbacks:
    """Callbacks para controlar y optimizar el pipeline RAG."""

    def __init__(self):
        self.current_config = self._load_current_config()
        self.config_file_path = "app/common/rag_config.json"

    def _load_current_config(self) -> Dict[str, Any]:
        """Carga la configuración actual del pipeline RAG."""
        
        default_config = {
            "chunk_size": 1200,
            "chunk_overlap": 200,
            "max_context_docs": 5,
            "embedding_model": "sentence-transformers/all-mpnet-base-v2",
            "temperature": 0.7,
            "max_tokens": 1000,
            "retrieval_strategy": "similarity",
            "rerank_enabled": False,
            "cache_enabled": True,
            "cache_size": 1000
        }
        
        try:
            config_path = "app/common/rag_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            logger.warning(f"Could not load RAG config: {e}")
        
        return default_config

    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Guarda la configuración del pipeline RAG."""
        
        try:
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            with open(self.config_file_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Could not save RAG config: {e}")
            return False

    def update_chunking_strategy(self, parameters: Dict[str, Any]) -> bool:
        """Actualiza la estrategia de chunking."""
        
        try:
            if "chunk_size" in parameters:
                chunk_size = int(parameters["chunk_size"])
                if 500 <= chunk_size <= 3000:
                    self.current_config["chunk_size"] = chunk_size
                    logger.info(f"Updated chunk_size to {chunk_size}")
                else:
                    logger.warning(f"Invalid chunk_size: {chunk_size}")
                    return False
            
            if "chunk_overlap" in parameters:
                overlap = int(parameters["chunk_overlap"])
                if 0 <= overlap <= 500:
                    self.current_config["chunk_overlap"] = overlap
                    logger.info(f"Updated chunk_overlap to {overlap}")
                else:
                    logger.warning(f"Invalid chunk_overlap: {overlap}")
                    return False
            
            return self._save_config(self.current_config)
            
        except Exception as e:
            logger.error(f"Error updating chunking strategy: {e}")
            return False

    def update_retrieval_config(self, parameters: Dict[str, Any]) -> bool:
        """Actualiza la configuración de recuperación."""
        
        try:
            if "max_context_docs" in parameters:
                max_docs = int(parameters["max_context_docs"])
                if 1 <= max_docs <= 20:
                    self.current_config["max_context_docs"] = max_docs
                    logger.info(f"Updated max_context_docs to {max_docs}")
                else:
                    logger.warning(f"Invalid max_context_docs: {max_docs}")
                    return False
            
            if "retrieval_strategy" in parameters:
                strategy = str(parameters["retrieval_strategy"])
                valid_strategies = ["similarity", "mmr", "similarity_score_threshold"]
                if strategy in valid_strategies:
                    self.current_config["retrieval_strategy"] = strategy
                    logger.info(f"Updated retrieval_strategy to {strategy}")
                else:
                    logger.warning(f"Invalid retrieval_strategy: {strategy}")
                    return False
            
            if "rerank_enabled" in parameters:
                rerank = bool(parameters["rerank_enabled"])
                self.current_config["rerank_enabled"] = rerank
                logger.info(f"Updated rerank_enabled to {rerank}")
            
            return self._save_config(self.current_config)
            
        except Exception as e:
            logger.error(f"Error updating retrieval config: {e}")
            return False

    def update_llm_config(self, parameters: Dict[str, Any]) -> bool:
        """Actualiza la configuración del LLM."""
        
        try:
            if "temperature" in parameters:
                temp = float(parameters["temperature"])
                if 0.0 <= temp <= 2.0:
                    self.current_config["temperature"] = temp
                    logger.info(f"Updated temperature to {temp}")
                else:
                    logger.warning(f"Invalid temperature: {temp}")
                    return False
            
            if "max_tokens" in parameters:
                max_tokens = int(parameters["max_tokens"])
                if 100 <= max_tokens <= 4000:
                    self.current_config["max_tokens"] = max_tokens
                    logger.info(f"Updated max_tokens to {max_tokens}")
                else:
                    logger.warning(f"Invalid max_tokens: {max_tokens}")
                    return False
            
            return self._save_config(self.current_config)
            
        except Exception as e:
            logger.error(f"Error updating LLM config: {e}")
            return False

    def update_embedding_config(self, parameters: Dict[str, Any]) -> bool:
        """Actualiza la configuración de embeddings."""
        
        try:
            if "embedding_model" in parameters:
                model = str(parameters["embedding_model"])
                valid_models = [
                    "sentence-transformers/all-mpnet-base-v2",
                    "sentence-transformers/all-MiniLM-L6-v2",
                    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                    "sentence-transformers/distiluse-base-multilingual-cased"
                ]
                
                if model in valid_models:
                    self.current_config["embedding_model"] = model
                    logger.info(f"Updated embedding_model to {model}")
                else:
                    logger.warning(f"Invalid embedding_model: {model}")
                    return False
            
            return self._save_config(self.current_config)
            
        except Exception as e:
            logger.error(f"Error updating embedding config: {e}")
            return False

    def update_cache_config(self, parameters: Dict[str, Any]) -> bool:
        """Actualiza la configuración de caché."""
        
        try:
            if "cache_enabled" in parameters:
                cache_enabled = bool(parameters["cache_enabled"])
                self.current_config["cache_enabled"] = cache_enabled
                logger.info(f"Updated cache_enabled to {cache_enabled}")
            
            if "cache_size" in parameters:
                cache_size = int(parameters["cache_size"])
                if 100 <= cache_size <= 10000:
                    self.current_config["cache_size"] = cache_size
                    logger.info(f"Updated cache_size to {cache_size}")
                else:
                    logger.warning(f"Invalid cache_size: {cache_size}")
                    return False
            
            if "embedding_cache_size" in parameters:
                emb_cache_size = int(parameters["embedding_cache_size"])
                if 100 <= emb_cache_size <= 5000:
                    self.current_config["embedding_cache_size"] = emb_cache_size
                    logger.info(f"Updated embedding_cache_size to {emb_cache_size}")
                else:
                    logger.warning(f"Invalid embedding_cache_size: {emb_cache_size}")
                    return False
            
            return self._save_config(self.current_config)
            
        except Exception as e:
            logger.error(f"Error updating cache config: {e}")
            return False

    def clear_cache(self, parameters: Dict[str, Any]) -> bool:
        """Limpia el caché del sistema."""
        
        try:
            cache_type = parameters.get("cache_type", "all")
            
            if cache_type in ["all", "embedding"]:
                # En implementación real, aquí se limpiaría el caché de embeddings
                logger.info("Cleared embedding cache")
            
            if cache_type in ["all", "retrieval"]:
                # En implementación real, aquí se limpiaría el caché de retrieval
                logger.info("Cleared retrieval cache")
            
            if cache_type in ["all", "llm"]:
                # En implementación real, aquí se limpiaría el caché del LLM
                logger.info("Cleared LLM cache")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def optimize_performance(self, parameters: Dict[str, Any]) -> bool:
        """Aplica optimizaciones de rendimiento generales."""
        
        try:
            optimization_level = parameters.get("optimization_level", "medium")
            
            if optimization_level == "low":
                # Optimizaciones conservadoras
                optimizations = {
                    "chunk_size": min(self.current_config["chunk_size"] + 100, 1500),
                    "max_context_docs": max(self.current_config["max_context_docs"] - 1, 3),
                    "cache_enabled": True
                }
            elif optimization_level == "medium":
                # Optimizaciones moderadas
                optimizations = {
                    "chunk_size": 1000,
                    "chunk_overlap": 150,
                    "max_context_docs": 4,
                    "rerank_enabled": True,
                    "cache_enabled": True,
                    "cache_size": 1500
                }
            else:  # high
                # Optimizaciones agresivas
                optimizations = {
                    "chunk_size": 800,
                    "chunk_overlap": 100,
                    "max_context_docs": 3,
                    "retrieval_strategy": "mmr",
                    "rerank_enabled": True,
                    "cache_enabled": True,
                    "cache_size": 2000,
                    "temperature": 0.5
                }
            
            # Aplicar optimizaciones
            self.current_config.update(optimizations)
            success = self._save_config(self.current_config)
            
            if success:
                logger.info(f"Applied {optimization_level} performance optimizations")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying performance optimizations: {e}")
            return False

    def rollback_config(self, parameters: Dict[str, Any]) -> bool:
        """Revierte la configuración a un estado anterior."""
        
        try:
            if "restore_config" in parameters:
                restore_config = parameters["restore_config"]
                if isinstance(restore_config, dict):
                    self.current_config = restore_config.copy()
                    success = self._save_config(self.current_config)
                    if success:
                        logger.info("Configuration rolled back successfully")
                    return success
            
            # Rollback a configuración por defecto
            self.current_config = self._load_current_config()
            logger.info("Configuration rolled back to default")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back configuration: {e}")
            return False

    def get_current_config(self) -> Dict[str, Any]:
        """Obtiene la configuración actual."""
        return self.current_config.copy()

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida una configuración antes de aplicarla."""
        
        try:
            # Validar chunk_size
            if "chunk_size" in config:
                if not (500 <= config["chunk_size"] <= 3000):
                    return False
            
            # Validar chunk_overlap
            if "chunk_overlap" in config:
                if not (0 <= config["chunk_overlap"] <= 500):
                    return False
            
            # Validar max_context_docs
            if "max_context_docs" in config:
                if not (1 <= config["max_context_docs"] <= 20):
                    return False
            
            # Validar temperature
            if "temperature" in config:
                if not (0.0 <= config["temperature"] <= 2.0):
                    return False
            
            # Validar max_tokens
            if "max_tokens" in config:
                if not (100 <= config["max_tokens"] <= 4000):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return False


# Instancia global para usar en callbacks
_rag_callbacks = RAGPipelineCallbacks()


def get_rag_pipeline_callback(component: str):
    """Obtiene el callback apropiado para un componente específico."""
    
    callback_map = {
        "rag_pipeline": _rag_callbacks.optimize_performance,
        "chunking": _rag_callbacks.update_chunking_strategy,
        "retrieval": _rag_callbacks.update_retrieval_config,
        "llm": _rag_callbacks.update_llm_config,
        "embeddings": _rag_callbacks.update_embedding_config,
        "cache": _rag_callbacks.update_cache_config,
        "cache_system": _rag_callbacks.clear_cache,
        "rollback": _rag_callbacks.rollback_config
    }
    
    return callback_map.get(component, _rag_callbacks.optimize_performance)
