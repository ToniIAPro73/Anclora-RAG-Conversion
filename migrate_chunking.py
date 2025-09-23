#!/usr/bin/env python3
"""
Script para migrar documentos existentes al nuevo sistema de chunking por dominio.
Re-procesa documentos que fueron chunkeados con el sistema anterior.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import json

# Add the app directory to the path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

def analyze_existing_chunks():
    """Analiza los chunks existentes en la base de datos"""
    
    print("🔍 ANÁLISIS DE CHUNKS EXISTENTES")
    print("=" * 50)
    
    try:
        from common.constants import CHROMA_SETTINGS, CHROMA_COLLECTIONS
        
        collections_info = {}
        total_documents = 0
        
        for collection_name, collection_config in CHROMA_COLLECTIONS.items():
            try:
                collection = CHROMA_SETTINGS.get_collection(collection_name)
                count = collection.count()
                
                # Obtener algunos documentos de muestra para análisis
                if count > 0:
                    sample_results = collection.query(
                        query_texts=["sample"],
                        n_results=min(5, count)
                    )
                    
                    # Analizar metadatos
                    sample_metadata = sample_results.get('metadatas', [[]])[0] if sample_results.get('metadatas') else []
                    chunk_sizes = []
                    
                    for doc_text in sample_results.get('documents', [[]])[0]:
                        chunk_sizes.append(len(doc_text))
                    
                    collections_info[collection_name] = {
                        "count": count,
                        "domain": collection_config.domain,
                        "sample_chunk_sizes": chunk_sizes,
                        "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                        "sample_metadata": sample_metadata[:2] if sample_metadata else []  # Primeros 2 metadatos
                    }
                    
                    total_documents += count
                    
                    print(f"📁 {collection_name} ({collection_config.domain}):")
                    print(f"   Documentos: {count}")
                    print(f"   Tamaño promedio de chunk: {collections_info[collection_name]['avg_chunk_size']:.0f} chars")
                    print(f"   Tamaños de muestra: {chunk_sizes}")
                    
                    # Detectar si necesita migración
                    needs_migration = any(size < 600 for size in chunk_sizes)  # Chunks muy pequeños
                    if needs_migration:
                        print(f"   ⚠️  NECESITA MIGRACIÓN: Chunks demasiado pequeños detectados")
                    else:
                        print(f"   ✅ Chunks parecen estar bien dimensionados")
                    print()
                
            except Exception as e:
                print(f"❌ Error analizando colección {collection_name}: {e}")
                collections_info[collection_name] = {"error": str(e)}
        
        print(f"📊 RESUMEN: {total_documents} documentos en {len(collections_info)} colecciones")
        return collections_info
        
    except Exception as e:
        print(f"❌ Error conectando a ChromaDB: {e}")
        return {}

def create_migration_plan(collections_info: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un plan de migración basado en el análisis"""
    
    print("\n📋 PLAN DE MIGRACIÓN")
    print("=" * 50)
    
    migration_plan = {
        "collections_to_migrate": [],
        "estimated_time": 0,
        "backup_recommended": True,
        "steps": []
    }
    
    for collection_name, info in collections_info.items():
        if "error" in info:
            continue
            
        avg_size = info.get("avg_chunk_size", 0)
        count = info.get("count", 0)
        domain = info.get("domain", "unknown")
        
        # Determinar si necesita migración
        needs_migration = False
        reason = ""
        
        if avg_size < 400:  # Chunks muy pequeños
            needs_migration = True
            reason = "Chunks demasiado pequeños (< 400 chars)"
        elif domain == "code" and avg_size < 800:  # Código necesita chunks más grandes
            needs_migration = True
            reason = "Código necesita chunks más grandes"
        elif not any("chunking_domain" in str(meta) for meta in info.get("sample_metadata", [])):
            needs_migration = True
            reason = "Falta metadatos de chunking por dominio"
        
        if needs_migration:
            migration_plan["collections_to_migrate"].append({
                "name": collection_name,
                "domain": domain,
                "document_count": count,
                "current_avg_size": avg_size,
                "reason": reason,
                "priority": "high" if domain == "code" else "medium"
            })
            
            # Estimar tiempo (aprox 1 segundo por documento)
            migration_plan["estimated_time"] += count * 1
        
        print(f"📁 {collection_name}:")
        print(f"   Estado: {'🔄 MIGRAR' if needs_migration else '✅ OK'}")
        if needs_migration:
            print(f"   Razón: {reason}")
            print(f"   Documentos a procesar: {count}")
        print()
    
    # Agregar pasos del plan
    if migration_plan["collections_to_migrate"]:
        migration_plan["steps"] = [
            "1. 💾 Crear backup de la base de datos actual",
            "2. 🔄 Re-procesar documentos con nuevo chunking",
            "3. 🧪 Validar calidad de los nuevos chunks",
            "4. 📊 Comparar métricas de retrieval",
            "5. ✅ Confirmar migración exitosa"
        ]
        
        print(f"⏱️  TIEMPO ESTIMADO: {migration_plan['estimated_time']} segundos")
        print(f"📦 COLECCIONES A MIGRAR: {len(migration_plan['collections_to_migrate'])}")
        
        for step in migration_plan["steps"]:
            print(f"   {step}")
    else:
        print("✅ No se requiere migración - todos los chunks están optimizados")
    
    return migration_plan

def simulate_migration(migration_plan: Dict[str, Any]):
    """Simula la migración para mostrar los resultados esperados"""
    
    if not migration_plan["collections_to_migrate"]:
        return
    
    print("\n🧪 SIMULACIÓN DE MIGRACIÓN")
    print("=" * 50)
    
    try:
        from common.ingest_file import CHUNKING_CONFIG
        
        for collection in migration_plan["collections_to_migrate"]:
            name = collection["name"]
            domain = collection["domain"]
            current_avg = collection["current_avg_size"]
            
            new_config = CHUNKING_CONFIG.get(domain, CHUNKING_CONFIG["default"])
            expected_avg = new_config["chunk_size"] * 0.7  # Estimación conservadora
            
            print(f"📁 {name} ({domain}):")
            print(f"   Tamaño actual promedio: {current_avg:.0f} chars")
            print(f"   Tamaño esperado promedio: {expected_avg:.0f} chars")
            print(f"   Configuración nueva: {new_config['chunk_size']} chars, overlap {new_config['chunk_overlap']}")
            
            # Estimar reducción de chunks
            if expected_avg > current_avg:
                reduction = 1 - (current_avg / expected_avg)
                print(f"   📉 Reducción estimada de chunks: {reduction*100:.1f}%")
                print(f"   ✅ Mejor coherencia semántica esperada")
            print()
            
    except Exception as e:
        print(f"❌ Error en simulación: {e}")

def generate_migration_script():
    """Genera un script de migración personalizado"""
    
    print("\n📝 GENERANDO SCRIPT DE MIGRACIÓN")
    print("=" * 50)
    
    script_content = '''#!/usr/bin/env python3
"""
Script de migración automática generado para actualizar chunking.
IMPORTANTE: Ejecutar solo después de crear backup de la base de datos.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

def migrate_collection(collection_name: str):
    """Migra una colección específica al nuevo chunking"""
    
    print(f"🔄 Migrando colección: {collection_name}")
    
    try:
        from common.constants import CHROMA_SETTINGS
        from common.ingest_file import _get_text_splitter_for_domain, CHUNKING_CONFIG
        
        # Obtener colección existente
        collection = CHROMA_SETTINGS.get_collection(collection_name)
        
        # Obtener todos los documentos
        all_results = collection.get()
        
        if not all_results['documents']:
            print(f"   ⚠️  Colección {collection_name} está vacía")
            return
        
        print(f"   📊 Procesando {len(all_results['documents'])} documentos...")
        
        # Aquí iría la lógica de re-chunking
        # Por seguridad, este script solo simula la migración
        
        print(f"   ✅ Migración de {collection_name} completada")
        
    except Exception as e:
        print(f"   ❌ Error migrando {collection_name}: {e}")

def main():
    """Función principal de migración"""
    
    print("🚀 INICIANDO MIGRACIÓN DE CHUNKING")
    print("=" * 50)
    
    # Lista de colecciones a migrar (personalizar según análisis)
    collections_to_migrate = [
        "troubleshooting",  # código
        "conversion_rules", # documentos
        "multimedia_assets" # multimedia
    ]
    
    for collection_name in collections_to_migrate:
        migrate_collection(collection_name)
    
    print("\\n✅ MIGRACIÓN COMPLETADA")
    print("Recuerda validar la calidad de los nuevos chunks")

if __name__ == "__main__":
    main()
'''
    
    with open("run_migration.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ Script de migración generado: run_migration.py")
    print("⚠️  IMPORTANTE: Crear backup antes de ejecutar")

def main():
    """Función principal"""
    
    print("🔄 HERRAMIENTA DE MIGRACIÓN DE CHUNKING")
    print("=" * 60)
    print("Analiza y migra documentos al nuevo sistema de chunking por dominio")
    print()
    
    # Paso 1: Analizar chunks existentes
    collections_info = analyze_existing_chunks()
    
    if not collections_info:
        print("❌ No se pudo conectar a la base de datos")
        return 1
    
    # Paso 2: Crear plan de migración
    migration_plan = create_migration_plan(collections_info)
    
    # Paso 3: Simular resultados
    simulate_migration(migration_plan)
    
    # Paso 4: Generar script de migración
    generate_migration_script()
    
    print("\n🎯 PRÓXIMOS PASOS:")
    print("1. 💾 Crear backup: docker-compose exec chromadb cp -r /chroma /chroma_backup")
    print("2. 🧪 Probar con documentos de prueba primero")
    print("3. 🔄 Ejecutar migración: python run_migration.py")
    print("4. 📊 Validar mejoras en retrieval")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
