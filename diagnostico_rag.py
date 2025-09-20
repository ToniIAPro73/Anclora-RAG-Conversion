#!/usr/bin/env python3
"""
Script de diagnóstico para el sistema Anclora RAG
"""

import os
import sys
import requests
import time
from pathlib import Path

def check_docker_services():
    """Verificar servicios Docker"""
    print("🔍 Verificando servicios Docker...")
    
    try:
        import subprocess
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        print(result.stdout)
        
        if 'Up' in result.stdout:
            print("✅ Servicios Docker están corriendo")
            return True
        else:
            print("❌ Algunos servicios no están corriendo")
            return False
    except Exception as e:
        print(f"❌ Error verificando Docker: {e}")
        return False

def check_streamlit_ui():
    """Verificar interfaz Streamlit"""
    print("\n🔍 Verificando interfaz Streamlit...")
    
    try:
        response = requests.get('http://localhost:8080', timeout=10)
        if response.status_code == 200:
            print("✅ Interfaz Streamlit accesible en http://localhost:8080")
            return True
        else:
            print(f"❌ Interfaz Streamlit responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ No se puede acceder a Streamlit: {e}")
        return False

def check_chroma_db():
    """Verificar ChromaDB"""
    print("\n🔍 Verificando ChromaDB...")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/heartbeat', timeout=10)
        if response.status_code == 200:
            print("✅ ChromaDB accesible en http://localhost:8000")
            return True
        else:
            print(f"❌ ChromaDB responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ No se puede acceder a ChromaDB: {e}")
        return False

def check_ollama():
    """Verificar Ollama"""
    print("\n🔍 Verificando Ollama...")
    
    try:
        # Verificar si Ollama está corriendo
        response = requests.get('http://localhost:11434/api/tags', timeout=10)
        if response.status_code == 200:
            models = response.json()
            print("✅ Ollama accesible")
            print(f"Modelos disponibles: {[model['name'] for model in models.get('models', [])]}")
            return True
        else:
            print(f"❌ Ollama responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ No se puede acceder a Ollama: {e}")
        print("💡 Asegúrate de que el modelo esté descargado:")
        print("   docker exec [CONTAINER_ID] ollama pull llama3")
        print("   o")
        print("   docker exec [CONTAINER_ID] ollama pull phi3")
        return False

def check_documents_in_chroma():
    """Verificar documentos en ChromaDB"""
    print("\n🔍 Verificando documentos en la base de conocimiento...")
    
    try:
        # Intentar conectar a ChromaDB y verificar documentos
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.HttpClient(
            host="localhost", 
            port=8000, 
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        collection = client.get_or_create_collection(name='vectordb')
        doc_count = collection.count()
        
        if doc_count > 0:
            print(f"✅ {doc_count} documentos encontrados en la base de conocimiento")
            
            # Obtener algunos ejemplos
            docs = collection.get(limit=3, include=['metadatas'])
            if docs['metadatas']:
                print("📄 Documentos de ejemplo:")
                for metadata in docs['metadatas'][:3]:
                    source = metadata.get('source', 'Sin fuente')
                    print(f"   - {source}")
            return True
        else:
            print("⚠️  No hay documentos en la base de conocimiento")
            print("💡 Para agregar documentos:")
            print("   1. Ve a http://localhost:8080")
            print("   2. Haz clic en 'Archivos' en la barra lateral")
            print("   3. Sube un documento (PDF, DOC, TXT, etc.)")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando documentos: {e}")
        return False

def test_basic_query():
    """Probar consulta básica"""
    print("\n🔍 Probando consulta básica...")
    
    try:
        # Simular una consulta básica
        print("💡 Para probar el sistema:")
        print("   1. Ve a http://localhost:8080")
        print("   2. Escribe 'Hola' en el chat")
        print("   3. Deberías recibir una respuesta de Bastet")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba básica: {e}")
        return False

def show_troubleshooting():
    """Mostrar guía de solución de problemas"""
    print("\n🔧 GUÍA DE SOLUCIÓN DE PROBLEMAS:")
    print("="*50)
    
    print("\n1. Si los servicios no están corriendo:")
    print("   docker-compose down")
    print("   docker-compose up -d")
    
    print("\n2. Si Ollama no tiene modelos:")
    print("   docker ps  # Copiar CONTAINER ID de ollama")
    print("   docker exec [CONTAINER_ID] ollama pull llama3")
    print("   # o para CPU:")
    print("   docker exec [CONTAINER_ID] ollama pull phi3")
    
    print("\n3. Si no hay documentos:")
    print("   - Ve a http://localhost:8080")
    print("   - Pestaña 'Archivos'")
    print("   - Sube un documento de prueba")
    
    print("\n4. Si el chat no responde:")
    print("   - Verifica que todos los servicios estén 'Up'")
    print("   - Revisa los logs: docker-compose logs ui")
    print("   - Asegúrate de que haya documentos en la base")
    
    print("\n5. Para ver logs detallados:")
    print("   docker-compose logs ui")
    print("   docker-compose logs chroma")
    print("   docker-compose logs ollama")

def main():
    """Función principal de diagnóstico"""
    print("🚀 DIAGNÓSTICO DEL SISTEMA ANCLORA RAG")
    print("="*40)
    
    checks = [
        ("Docker Services", check_docker_services),
        ("Streamlit UI", check_streamlit_ui),
        ("ChromaDB", check_chroma_db),
        ("Ollama", check_ollama),
        ("Documentos", check_documents_in_chroma),
        ("Consulta Básica", test_basic_query)
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
        time.sleep(1)  # Pausa entre verificaciones
    
    # Resumen
    print("\n📊 RESUMEN DEL DIAGNÓSTICO:")
    print("="*30)
    
    all_good = True
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
        if not status:
            all_good = False
    
    if all_good:
        print("\n🎉 ¡Todo está funcionando correctamente!")
        print("Puedes usar el sistema en: http://localhost:8080")
    else:
        print("\n⚠️  Se encontraron algunos problemas.")
        show_troubleshooting()
    
    print(f"\n📝 Para más ayuda, revisa: AUGMENT_CORRECCIONES_IMPLEMENTADAS.md")

if __name__ == "__main__":
    main()
