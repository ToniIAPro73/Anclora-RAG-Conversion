"""
Mapeo inteligente de campos entre diferentes formatos
"""

import re
from typing import Dict, List, Optional

class FieldMapper:
    def __init__(self):
        # Mapeo de campos NotebookLM → Anclora
        self.field_mapping = {
            r'(?i)(source|fuente|document)': 'Titulo',
            r'(?i)(type|tipo)': 'Tipo',
            r'(?i)(author|autor|writer)': 'Autor(es)',
            r'(?i)(publisher|editorial|journal)': 'Editorial/Origen',
            r'(?i)(year|año|date|fecha)': 'Anio',
            r'(?i)(url|doi|link|enlace)': 'URL/DOI/Identificador',
            r'(?i)(citation|cita|reference)': 'Citacion',
            r'(?i)(origin|origen|source doc)': 'Documento_Fuente'
        }
        
        # Normalización de tipos
        self.type_normalization = {
            'academic paper': 'Articulo Academico',
            'research paper': 'Articulo Academico',
            'journal article': 'Articulo Academico',
            'book': 'Libro',
            'web page': 'Pagina Web',
            'software tool': 'Herramienta Software',
            'conference paper': 'Paper de Conferencia',
            'thesis': 'Tesis',
            'technical report': 'Reporte Tecnico',
            'blog post': 'Post de Blog',
            'online resource': 'Recurso Online'
        }
    
    def map_fields(self, source_block: str, source_index: int) -> Dict[str, str]:
        """Mapea un bloque de fuente a formato Anclora"""
        mapped_fields = {
            'ID': f"SRC-{source_index:03d}",
            'Tipo': 'N/A',
            'Titulo': 'N/A',
            'Autor(es)': 'N/A',
            'Editorial/Origen': 'N/A',
            'Anio': 'N/A',
            'URL/DOI/Identificador': 'N/A',
            'Citacion': 'N/A',
            'Documento_Fuente': 'NotebookLM_Export.md'
        }
        
        # Extraer título (generalmente la primera línea en negrita)
        title_match = re.search(r'^\d+\.\s+\*\*(.+?)\*\*', source_block)
        if title_match:
            mapped_fields['Titulo'] = title_match.group(1).strip()
        else:
            # Intentar otro patrón común
            title_match = re.search(r'^- \*\*Source:\*\*\s*(.+)$', source_block, re.MULTILINE)
            if title_match:
                mapped_fields['Titulo'] = title_match.group(1).strip()
        
        # Mapear campos específicos
        for notebook_pattern, anclora_field in self.field_mapping.items():
            pattern = re.compile(fr'{notebook_pattern}[:\s]*([^\n]+)', re.IGNORECASE)
            match = pattern.search(source_block)
            if match:
                value = match.group(1).strip().strip('*').strip()
                # Normalizar tipos
                if anclora_field == 'Tipo' and value.lower() in self.type_normalization:
                    value = self.type_normalization[value.lower()]
                mapped_fields[anclora_field] = value
        
        # Limpieza final de valores
        for key in mapped_fields:
            if mapped_fields[key] != 'N/A':
                mapped_fields[key] = mapped_fields[key].strip()
        
        return mapped_fields
    
    def extract_source_blocks(self, content: str) -> List[str]:
        """Extrae bloques individuales de fuentes del contenido"""
        # Diferentes patrones para dividir fuentes
        patterns = [
            r'(\d+\.\s+\*\*.+?\*\*)(.*?)(?=\n\s*\d+\.\s+\*\*|\Z)',
            r'(^- \*\*Source:\*\*.+?)(?=^- \*\*Source:\*\*|\Z)',
            r'(\n#{2,}\s+.+?)(?=\n#{2,}\s+|\Z)'
        ]
        
        blocks = []
        for pattern in patterns:
            found_blocks = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if found_blocks:
                # Si encontramos bloques, tomar el contenido principal (grupo 2 o grupo 1)
                if len(found_blocks[0]) > 1:
                    blocks = [block[1] if len(block) > 1 else block[0] for block in found_blocks]
                else:
                    blocks = found_blocks
                
                if len(blocks) >= 3:  # Mínimo 3 fuentes para considerar el patrón válido
                    break
        
        # Fallback: dividir por líneas que empiezan con números
        if not blocks:
            lines = content.split('\n')
            current_block = []
            blocks = []
            
            for line in lines:
                if re.match(r'^\d+\.', line.strip()):
                    if current_block:
                        blocks.append('\n'.join(current_block))
                        current_block = []
                current_block.append(line)
            
            if current_block:
                blocks.append('\n'.join(current_block))
        
        return blocks
