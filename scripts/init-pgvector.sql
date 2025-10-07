-- =============================================================================
-- Inicialización de PostgreSQL con pgvector para Anclora RAG
-- =============================================================================
-- Este script se ejecuta automáticamente cuando se inicia PostgreSQL
-- Configura la extensión pgvector y optimizaciones de rendimiento
-- =============================================================================

-- Crear extensión pgvector si no existe
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear extensión pg_stat_statements para monitoreo de consultas
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Configurar parámetros de memoria para mejor rendimiento con vectores
-- Estos valores se pueden ajustar según los recursos disponibles

-- Crear base de datos si no existe (aunque ya se crea por environment)
-- Esta consulta es segura de ejecutar múltiples veces
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = current_setting('POSTGRES_DB')) THEN
      CREATE DATABASE current_setting('POSTGRES_DB');
   END IF;
END
$$;

-- Conectar a la base de datos específica
\c anclora_rag;

-- Crear esquema para tablas de LangChain/Pgvector si no existe
CREATE SCHEMA IF NOT EXISTS langchain;

-- Configurar permisos para el usuario de la aplicación
GRANT USAGE ON SCHEMA langchain TO anclora_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA langchain TO anclora_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA langchain TO anclora_user;

-- Crear índices optimizados para búsquedas vectoriales
-- Estos índices se crean automáticamente cuando se usan las tablas,
-- pero podemos preparar funciones útiles

-- Función para calcular distancia coseno (útil para debugging)
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float8 AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql;

-- Función para buscar documentos similares con límite
CREATE OR REPLACE FUNCTION find_similar_documents(
    query_embedding vector(384),  -- Ajustar dimensión según modelo de embeddings
    collection_name text,
    limit_count integer DEFAULT 5
)
RETURNS TABLE(
    document text,
    metadata jsonb,
    similarity float8
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        lpe.document,
        lpe.metadata,
        cosine_similarity(query_embedding, lpe.embedding) as similarity
    FROM langchain.langchain_pg_embedding lpe
    WHERE lpe.collection_id = (
        SELECT collection_id
        FROM langchain.langchain_pg_collection
        WHERE name = collection_name
        LIMIT 1
    )
    ORDER BY lpe.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Comentarios para documentación
COMMENT ON EXTENSION vector IS 'pgvector extension for vector similarity search';
COMMENT ON FUNCTION cosine_similarity(vector, vector) IS 'Calculate cosine similarity between two vectors';
COMMENT ON FUNCTION find_similar_documents(vector, text, integer) IS 'Find similar documents using vector similarity search';

-- Log de inicialización completada
DO $$
BEGIN
    RAISE NOTICE 'pgvector initialization completed successfully';
    RAISE NOTICE 'Available functions: cosine_similarity, find_similar_documents';
    RAISE NOTICE 'Schema langchain configured for user anclora_user';
END $$;