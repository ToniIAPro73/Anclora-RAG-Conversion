"""
Script para ejecutar el scraping de fuentes automáticamente
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.data_ingestion.source_scraper import scrape_all_sources
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

async def main():
    """Función principal"""
    
    print("🚀 Iniciando scraping automático de fuentes para RAG")
    print("=" * 60)
    
    # Ruta al documento de fuentes
    doc_path = "docs/Informe de fuentes sistema RAG multiagente conversor inteligente.docx.md"
    
    if not os.path.exists(doc_path):
        print(f"❌ Error: No se encuentra el documento en {doc_path}")
        return
    
    try:
        # Ejecutar scraping
        results = await scrape_all_sources(doc_path)
        
        # Mostrar resultados
        print("\n📊 RESULTADOS DEL SCRAPING")
        print("=" * 40)
        print(f"📚 Total fuentes encontradas: {results['total_sources']}")
        print(f"✅ Procesadas exitosamente: {results['successful']}")
        print(f"❌ Fallidas: {results['failed']}")
        print(f"📈 Tasa de éxito: {(results['successful']/results['total_sources']*100):.1f}%")
        
        # Mostrar estadísticas por tipo
        print(f"\n📁 Archivos guardados en: data/scraped_sources/")
        print("   - PDFs: data/scraped_sources/pdfs/")
        print("   - Artículos: data/scraped_sources/articles/")
        print("   - Documentos: data/scraped_sources/docs/")
        
        print(f"\n🎯 ¡Scraping completado! Ahora puedes alimentar el RAG con estos datos.")
        
    except Exception as e:
        print(f"❌ Error durante el scraping: {str(e)}")
        logging.error(f"Error en scraping: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
