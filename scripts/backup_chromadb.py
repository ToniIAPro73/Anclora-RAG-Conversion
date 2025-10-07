#!/usr/bin/env python3
"""
Script de respaldo automático de ChromaDB antes de la migración
Crea respaldos en formato JSON y pickle para recuperación de emergencia
"""

import os
import sys
import json
import pickle
import logging
from datetime import datetime
from typing import Dict, Any
import chromadb
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def create_backup_directory() -> str:
    """Crear directorio de respaldos con timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/chromadb_backup_{timestamp}"

    os.makedirs(backup_dir, exist_ok=True)
    logger.info(f"Directorio de respaldo creado: {backup_dir}")
    return backup_dir

def backup_collection_to_json(collection, backup_dir: str) -> bool:
    """Respaldar colección a formato JSON"""
    try:
        collection_name = collection.name
        logger.info(f"Respaldando colección {collection_name} a JSON...")

        # Obtener todos los documentos
        count = collection.count()
        if count == 0:
            logger.warning(f"Colección {collection_name} está vacía")
            return True

        # Obtener documentos en lotes
        all_data = []
        limit = 1000
        offset = 0

        while offset < count:
            results = collection.get(limit=limit, offset=offset, include=['documents', 'metadatas', 'embeddings'])
            if not results['documents']:
                break

            for i, doc in enumerate(results['documents']):
                item = {
                    'id': results['ids'][i],
                    'document': doc,
                    'metadata': results['metadatas'][i] if results['metadatas'] and i < len(results['metadatas']) else {},
                    'embedding': results['embeddings'][i] if results['embeddings'] and i < len(results['embeddings']) else None
                }
                all_data.append(item)

            offset += limit
            logger.info(f"Procesados {len(all_data)} documentos de {collection_name}")

        # Guardar como JSON
        json_file = os.path.join(backup_dir, f"{collection_name}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Respaldo JSON creado: {json_file}")
        return True

    except Exception as e:
        logger.error(f"❌ Error respaldando colección {collection_name}: {e}")
        return False

def backup_collection_to_pickle(collection, backup_dir: str) -> bool:
    """Respaldar colección a formato pickle (más rápido para restauración)"""
    try:
        collection_name = collection.name
        logger.info(f"Respaldando colección {collection_name} a pickle...")

        # Obtener todos los documentos
        count = collection.count()
        if count == 0:
            logger.warning(f"Colección {collection_name} está vacía")
            return True

        # Obtener documentos en lotes
        all_data = []
        limit = 1000
        offset = 0

        while offset < count:
            results = collection.get(limit=limit, offset=offset, include=['documents', 'metadatas', 'embeddings'])
            if not results['documents']:
                break

            for i, doc in enumerate(results['documents']):
                item = {
                    'id': results['ids'][i],
                    'document': doc,
                    'metadata': results['metadatas'][i] if results['metadatas'] and i < len(results['metadatas']) else {},
                    'embedding': results['embeddings'][i] if results['embeddings'] and i < len(results['embeddings']) else None
                }
                all_data.append(item)

            offset += limit

        # Guardar como pickle
        pickle_file = os.path.join(backup_dir, f"{collection_name}.pkl")
        with open(pickle_file, 'wb') as f:
            pickle.dump(all_data, f)

        logger.info(f"✅ Respaldo pickle creado: {pickle_file}")
        return True

    except Exception as e:
        logger.error(f"❌ Error respaldando colección {collection_name}: {e}")
        return False

def create_metadata_backup(backup_dir: str):
    """Crear archivo de metadatos del respaldo"""
    try:
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'chromadb_host': os.getenv("CHROMA_HOST", "localhost"),
            'chromadb_port': os.getenv("CHROMA_PORT", "8000"),
            'backup_type': 'chromadb_migration_preparation',
            'description': 'Respaldo automático antes de migración a Pgvector'
        }

        metadata_file = os.path.join(backup_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Metadatos creados: {metadata_file}")

    except Exception as e:
        logger.error(f"❌ Error creando metadatos: {e}")

def main():
    """Función principal de respaldo"""
    logger.info("💾 Iniciando respaldo completo de ChromaDB...")

    # Crear directorio de respaldo
    backup_dir = create_backup_directory()

    # Conectar a ChromaDB
    try:
        client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000"))
        )
    except Exception as e:
        logger.error(f"❌ Error conectando a ChromaDB: {e}")
        return False

    # Obtener colecciones
    try:
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
    except Exception as e:
        logger.error(f"❌ Error obteniendo colecciones: {e}")
        return False

    if not collection_names:
        logger.warning("⚠️ No se encontraron colecciones para respaldar")
        return True

    logger.info(f"📋 Colecciones encontradas: {collection_names}")

    # Respaldar cada colección
    success_count = 0

    for collection_name in collection_names:
        try:
            collection = client.get_collection(collection_name)

            # Crear respaldo JSON
            if backup_collection_to_json(collection, backup_dir):
                success_count += 1

            # Crear respaldo pickle
            if backup_collection_to_pickle(collection, backup_dir):
                success_count += 1

        except Exception as e:
            logger.error(f"❌ Error procesando colección {collection_name}: {e}")

    # Crear metadatos
    create_metadata_backup(backup_dir)

    # Resumen final
    total_backups = len(collection_names) * 2  # JSON + pickle por colección
    logger.info(f"✅ Respaldo completado: {success_count}/{total_backups} archivos creados")
    logger.info(f"📁 Ubicación del respaldo: {backup_dir}")

    if success_count == total_backups:
        logger.info("🎉 ¡Respaldo completamente exitoso!")
        logger.info("💡 Puedes proceder con la migración a Pgvector")
    else:
        logger.warning("⚠️ Algunos respaldos fallaron, pero puedes continuar con la migración")

    return success_count == total_backups

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)