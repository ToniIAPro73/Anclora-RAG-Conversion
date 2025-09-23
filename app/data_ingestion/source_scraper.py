"""
Scraper Automático de Fuentes para RAG - Anclora RAG
Extrae y procesa automáticamente las 240+ fuentes del documento
"""

import asyncio
import aiohttp
import aiofiles
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import hashlib
import json
from datetime import datetime
import logging

# Imports para procesamiento
import requests
from bs4 import BeautifulSoup
import PyPDF2
import docx
import markdown

logger = logging.getLogger(__name__)

@dataclass
class Source:
    """Fuente de datos identificada"""
    title: str
    source_type: str  # "Artículo Académico", "Blog Técnico", etc.
    contribution: str
    url: Optional[str] = None
    file_path: Optional[str] = None
    category: str = "general"
    priority: int = 1  # 1=alta, 2=media, 3=baja

class SourceScraper:
    """Scraper inteligente para extraer fuentes automáticamente"""
    
    def __init__(self, output_dir: str = "data/scraped_sources"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Directorios por tipo
        self.dirs = {
            'pdfs': self.output_dir / 'pdfs',
            'articles': self.output_dir / 'articles', 
            'repos': self.output_dir / 'repos',
            'docs': self.output_dir / 'docs',
            'failed': self.output_dir / 'failed'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Estadísticas
        self.stats = {
            'total_sources': 0,
            'processed': 0,
            'failed': 0,
            'by_type': {}
        }
    
    async def parse_sources_document(self, doc_path: str) -> List[Source]:
        """Parsea el documento de fuentes y extrae todas las referencias"""
        
        logger.info(f"📖 Parseando documento: {doc_path}")
        
        async with aiofiles.open(doc_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        sources = []
        current_category = "general"
        
        # Regex patterns para extraer información
        title_pattern = r'\*\*Título del Documento o Identificador de la Fuente:\*\* "([^"]+)"'
        type_pattern = r'\*\*Tipo de Fuente:\*\* ([^\n]+)'
        contribution_pattern = r'\*\*Aportación Clave:\*\* ([^\n]+)'
        
        # Buscar secciones para categorizar
        section_pattern = r'## \*\*(\d+\.\d+) ([^*]+)\*\*'
        sections = re.findall(section_pattern, content)
        
        # Extraer todas las fuentes
        source_blocks = re.split(r'\* \*\*Título del Documento', content)[1:]
        
        for i, block in enumerate(source_blocks):
            block = "**Título del Documento" + block
            
            # Extraer información
            title_match = re.search(title_pattern, block)
            type_match = re.search(type_pattern, block)
            contribution_match = re.search(contribution_pattern, block)
            
            if title_match and type_match and contribution_match:
                title = title_match.group(1)
                source_type = type_match.group(1).strip()
                contribution = contribution_match.group(1).strip()
                
                # Detectar URLs en el título o contenido
                url = self._extract_url_from_text(block)
                
                # Determinar categoría basada en posición
                category = self._determine_category(i, len(source_blocks))
                
                # Determinar prioridad
                priority = self._determine_priority(source_type, title)
                
                source = Source(
                    title=title,
                    source_type=source_type,
                    contribution=contribution,
                    url=url,
                    category=category,
                    priority=priority
                )
                
                sources.append(source)
        
        logger.info(f"✅ Extraídas {len(sources)} fuentes")
        self.stats['total_sources'] = len(sources)
        
        return sources
    
    def _extract_url_from_text(self, text: str) -> Optional[str]:
        """Extrae URL del texto si existe"""
        
        # Patrones comunes de URLs
        url_patterns = [
            r'https?://[^\s\)]+',
            r'www\.[^\s\)]+',
            r'[a-zA-Z0-9.-]+\.com[^\s\)]*',
            r'[a-zA-Z0-9.-]+\.org[^\s\)]*',
            r'[a-zA-Z0-9.-]+\.edu[^\s\)]*'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        # Buscar referencias específicas
        if 'github.com' in text.lower():
            github_match = re.search(r'github\.com/[^\s\)]+', text, re.IGNORECASE)
            if github_match:
                return 'https://' + github_match.group(0)
        
        if 'arxiv' in text.lower():
            arxiv_match = re.search(r'arxiv\.org/[^\s\)]+', text, re.IGNORECASE)
            if arxiv_match:
                return 'https://' + arxiv_match.group(0)
        
        return None
    
    def _determine_category(self, index: int, total: int) -> str:
        """Determina categoría basada en posición en el documento"""
        
        # Aproximación basada en las secciones del documento
        if index < total * 0.3:
            return "document_processing"
        elif index < total * 0.6:
            return "ai_architectures"
        elif index < total * 0.8:
            return "tools_frameworks"
        else:
            return "compliance_optimization"
    
    def _determine_priority(self, source_type: str, title: str) -> int:
        """Determina prioridad de procesamiento"""
        
        high_priority_types = ["Artículo Académico", "Documentación Técnica", "Manual de Usuario"]
        high_priority_keywords = ["benchmark", "comparison", "evaluation", "framework"]
        
        if source_type in high_priority_types:
            return 1
        
        if any(keyword in title.lower() for keyword in high_priority_keywords):
            return 1
        
        if source_type in ["Blog Técnico", "Guía Técnica"]:
            return 2
        
        return 3
    
    async def process_all_sources(self, sources: List[Source]) -> Dict:
        """Procesa todas las fuentes automáticamente"""
        
        logger.info(f"🚀 Iniciando procesamiento de {len(sources)} fuentes")
        
        # Ordenar por prioridad
        sources.sort(key=lambda x: x.priority)
        
        # Procesar en lotes para no sobrecargar
        batch_size = 5
        results = []
        
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i+batch_size]
            logger.info(f"📦 Procesando lote {i//batch_size + 1}/{(len(sources)-1)//batch_size + 1}")
            
            batch_results = await asyncio.gather(
                *[self._process_single_source(source) for source in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            
            # Pausa entre lotes para ser respetuosos
            await asyncio.sleep(2)
        
        # Compilar estadísticas
        successful = [r for r in results if isinstance(r, dict) and r.get('success')]
        failed = [r for r in results if not (isinstance(r, dict) and r.get('success'))]
        
        self.stats['processed'] = len(successful)
        self.stats['failed'] = len(failed)
        
        # Guardar resultados
        await self._save_processing_results(results)
        
        logger.info(f"✅ Procesamiento completado: {len(successful)} exitosos, {len(failed)} fallidos")
        
        return {
            'total_sources': len(sources),
            'successful': len(successful),
            'failed': len(failed),
            'results': results,
            'stats': self.stats
        }
    
    async def _process_single_source(self, source: Source) -> Dict:
        """Procesa una fuente individual"""
        
        try:
            logger.info(f"🔄 Procesando: {source.title[:50]}...")
            
            if source.url:
                return await self._process_url_source(source)
            else:
                return await self._process_text_source(source)
                
        except Exception as e:
            logger.error(f"❌ Error procesando {source.title}: {str(e)}")
            return {
                'success': False,
                'source': source.title,
                'error': str(e)
            }
    
    async def _process_url_source(self, source: Source) -> Dict:
        """Procesa fuente con URL"""
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(source.url, timeout=30) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'pdf' in content_type:
                            return await self._save_pdf(source, await response.read())
                        elif 'html' in content_type:
                            return await self._save_html_article(source, await response.text())
                        else:
                            return await self._save_raw_content(source, await response.text())
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ URL fallida, guardando como texto: {source.title}")
            return await self._process_text_source(source)
    
    async def _process_text_source(self, source: Source) -> Dict:
        """Procesa fuente sin URL como texto estructurado"""
        
        # Crear contenido estructurado
        content = f"""# {source.title}

**Tipo de Fuente:** {source.source_type}
**Categoría:** {source.category}
**Prioridad:** {source.priority}

## Aportación Clave
{source.contribution}

## Metadatos
- Procesado: {datetime.now().isoformat()}
- URL Original: {source.url or 'No disponible'}
- Hash: {hashlib.md5(source.title.encode()).hexdigest()[:8]}
"""
        
        # Guardar como markdown
        filename = self._sanitize_filename(source.title) + '.md'
        file_path = self.dirs['docs'] / filename
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        return {
            'success': True,
            'source': source.title,
            'type': 'text',
            'file_path': str(file_path),
            'size': len(content)
        }
    
    async def _save_pdf(self, source: Source, content: bytes) -> Dict:
        """Guarda PDF y extrae texto"""
        
        filename = self._sanitize_filename(source.title) + '.pdf'
        file_path = self.dirs['pdfs'] / filename
        
        # Guardar PDF original
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Intentar extraer texto
        try:
            # Aquí usarías tu sistema de extracción de PDF
            extracted_text = f"PDF: {source.title}\n\nContenido extraído pendiente de procesamiento."
            
            # Guardar texto extraído
            text_path = self.dirs['docs'] / (self._sanitize_filename(source.title) + '_extracted.md')
            async with aiofiles.open(text_path, 'w', encoding='utf-8') as f:
                await f.write(extracted_text)
        
        except Exception as e:
            logger.warning(f"⚠️ No se pudo extraer texto del PDF: {e}")
        
        return {
            'success': True,
            'source': source.title,
            'type': 'pdf',
            'file_path': str(file_path),
            'size': len(content)
        }
    
    async def _save_html_article(self, source: Source, html_content: str) -> Dict:
        """Extrae y guarda contenido de artículo HTML"""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraer contenido principal
            title = soup.find('title')
            title_text = title.get_text() if title else source.title
            
            # Buscar contenido principal
            content_selectors = ['article', '.content', '.post', '.entry', 'main']
            main_content = None
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            # Limpiar y extraer texto
            if main_content:
                # Remover scripts y estilos
                for script in main_content(["script", "style"]):
                    script.decompose()
                
                text_content = main_content.get_text()
                # Limpiar espacios
                text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
                text_content = re.sub(r' +', ' ', text_content)
            else:
                text_content = "Contenido no extraíble"
            
            # Crear markdown estructurado
            markdown_content = f"""# {title_text}

**Fuente Original:** {source.url}
**Tipo:** {source.source_type}
**Categoría:** {source.category}

## Aportación Clave
{source.contribution}

## Contenido Extraído

{text_content}

---
*Extraído automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            # Guardar
            filename = self._sanitize_filename(source.title) + '.md'
            file_path = self.dirs['articles'] / filename
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(markdown_content)
            
            return {
                'success': True,
                'source': source.title,
                'type': 'article',
                'file_path': str(file_path),
                'size': len(markdown_content)
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando HTML: {e}")
            return await self._save_raw_content(source, html_content)
    
    async def _save_raw_content(self, source: Source, content: str) -> Dict:
        """Guarda contenido raw como fallback"""
        
        filename = self._sanitize_filename(source.title) + '_raw.txt'
        file_path = self.dirs['docs'] / filename
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(f"# {source.title}\n\n{content}")
        
        return {
            'success': True,
            'source': source.title,
            'type': 'raw',
            'file_path': str(file_path),
            'size': len(content)
        }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitiza nombre de archivo"""
        
        # Remover caracteres problemáticos
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\s-]', '', filename)
        filename = re.sub(r'[-\s]+', '_', filename)
        
        # Limitar longitud
        return filename[:100]
    
    async def _save_processing_results(self, results: List) -> None:
        """Guarda resultados del procesamiento"""
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'results': [r for r in results if isinstance(r, dict)]
        }
        
        results_path = self.output_dir / 'processing_results.json'
        async with aiofiles.open(results_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(summary, indent=2, ensure_ascii=False))
        
        logger.info(f"📊 Resultados guardados en: {results_path}")

# Función principal
async def scrape_all_sources(doc_path: str) -> Dict:
    """Función principal para scraper todas las fuentes"""
    
    scraper = SourceScraper()
    
    # 1. Parsear documento
    sources = await scraper.parse_sources_document(doc_path)
    
    # 2. Procesar todas las fuentes
    results = await scraper.process_all_sources(sources)
    
    return results
