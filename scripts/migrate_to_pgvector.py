#!/usr/bin/env python3
"""
Script de migración automática de ChromaDB a Pgvector
Ejecutar después de configurar PostgreSQL con pgvector
"""

import os
import sys
import logging
from typing import List, Dict, Any
import chromadb
from langchain_community.vectorstores import PGVector, Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_chroma_collections() -> List[str]:
    """Obtener lista de colecciones en ChromaDB"""
    try:
        client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000"))
        )
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        logger.error(f"Error conectando a ChromaDB: {e}")
        return []

def migrate_collection_to_pgvector(collection_name: str) -> bool:
    """Migrar una colección específica de ChromaDB a Pgvector"""
    try:
        logger.info(f"Migrando colección: {collection_name}")

        # Configurar embeddings
        embeddings = SentenceTransformerEmbeddings(
            model_name=os.getenv("EMBEDDINGS_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
        )

        # Conectar a ChromaDB
        chroma_client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000"))
        )

        # Crear colección ChromaDB si no existe
        try:
            collection = chroma_client.get_or_create_collection(collection_name)
        except Exception as e:
            logger.error(f"Error creando colección ChromaDB: {e}")
            return False

        # Obtener documentos de ChromaDB
        logger.info(f"Obteniendo documentos de colección {collection_name}...")
        count = collection.count()
        logger.info(f"Colección tiene {count} documentos")

        if count == 0:
            logger.warning(f"Colección {collection_name} está vacía, omitiendo")
            return True

        # Obtener todos los documentos (manejar paginación si es necesario)
        all_docs = []
        all_metadatas = []
        all_ids = []

        # ChromaDB puede tener límite de resultados, obtener en lotes
        limit = 1000
        offset = 0

        while offset < count:
            try:
                results = collection.get(limit=limit, offset=offset)
                if not results['documents']:
                    break

                all_docs.extend(results['documents'])
                all_metadatas.extend(results['metadatas'] or [{} for _ in results['documents']])
                all_ids.extend(results['ids'])

                offset += limit
                logger.info(f"Procesados {len(all_docs)} documentos...")

            except Exception as e:
                logger.error(f"Error obteniendo documentos: {e}")
                break

        logger.info(f"Total documentos obtenidos: {len(all_docs)}")

        # Configurar conexión Pgvector
        connection_string = PGVector.connection_string_from_db_params(
            driver="psycopg2",
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
        )

        # Crear tabla Pgvector
        pgvector = PGVector(
            collection_name=collection_name,
            connection_string=connection_string,
            embedding_function=embeddings,
        )

        # Crear tablas si no existen (Pgvector se encarga automáticamente)
        # PGVector crea las tablas automáticamente cuando se inicializa

        # Insertar documentos en Pgvector
        logger.info(f"Insertando {len(all_docs)} documentos en Pgvector...")
        pgvector.add_documents(
            documents=all_docs,
            metadatas=all_metadatas,
            ids=all_ids
        )

        logger.info(f"✅ Migración completada para colección: {collection_name}")
        return True

    except Exception as e:
        logger.error(f"❌ Error migrando colección {collection_name}: {e}")
        return False

def main():
    """Función principal de migración"""
    logger.info("🚀 Iniciando migración de ChromaDB a Pgvector...")

    # Verificar variables de entorno
    required_vars = ["PG_HOST", "PG_PORT", "PG_DB", "PG_USER", "PG_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        sys.exit(1)

    # Obtener colecciones de ChromaDB
    collections = get_chroma_collections()

    if not collections:
        logger.warning("No se encontraron colecciones en ChromaDB")
        return

    logger.info(f"Colecciones encontradas: {collections}")

    # Migrar cada colección
    success_count = 0
    for collection in collections:
        if migrate_collection_to_pgvector(collection):
            success_count += 1
        else:
            logger.error(f"Falló migración de colección: {collection}")

    logger.info(f"✅ Migración completada: {success_count}/{len(collections)} colecciones exitosas")

    if success_count == len(collections):
        logger.info("🎉 ¡Migración completamente exitosa!")
        logger.info("💡 Puedes detener y eliminar el servicio ChromaDB ahora")
    else:
        logger.warning("⚠️ Algunas migraciones fallaron, revisa los logs")

if __name__ == "__main__":
    main()