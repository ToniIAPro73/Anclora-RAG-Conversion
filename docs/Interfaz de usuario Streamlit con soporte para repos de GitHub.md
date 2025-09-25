Excelente idea. Voy a continuar el sistema de ingesta añadiendo soporte para repositorios de GitHub. Aquí está la continuación completa:

## 4. Interfaz de Usuario Streamlit (Continuación)

### `app/pages/02_📤_Ingesta_Avanzada.py` (Continuación)

```python
                # Detalles por categoría
                st.markdown("### 📊 Archivos por Categoría")
                
                categories_data = []
                for category, count in report['discovered_files']['by_category'].items():
                    if count > 0:
                        categories_data.append({
                            'Categoría': category.title(),
                            'Cantidad': count
                        })
                
                if categories_data:
                    df_categories = pd.DataFrame(categories_data)
                    
                    # Gráfico de barras
                    fig = px.bar(
                        df_categories,
                        x='Categoría',
                        y='Cantidad',
                        title='Distribución de Archivos por Tipo',
                        color='Cantidad',
                        color_continuous_scale='blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Recomendaciones
                if report['recommendations']:
                    st.markdown("### 💡 Recomendaciones")
                    for rec in report['recommendations']:
                        st.warning(rec)
                
                # Botón de procesamiento
                if st.button("🚀 Procesar Carpeta", type="primary", use_container_width=True):
                    with st.spinner(f"Procesando {report['discovered_files']['total']} archivos..."):
                        async def run_folder_ingestion():
                            job = await ingestion_system.ingest_folder(
                                folder_path=folder_path,
                                user_id=st.session_state.get('user_id', 'default'),
                                recursive=recursive,
                                metadata={'source': 'folder_upload'}
                            )
                            return job
                        
                        job = asyncio.run(run_folder_ingestion())
                        
                        # Mostrar resultados
                        if job.status == IngestionStatus.COMPLETED:
                            st.balloons()
                            st.success(f"✅ Carpeta procesada: {job.processed_files} archivos")
                        elif job.status == IngestionStatus.PARTIALLY_COMPLETED:
                            st.warning(f"⚠️ Procesamiento parcial: {job.processed_files}/{job.total_files}")
                        else:
                            st.error("❌ Error en el procesamiento")
    
    with col2:
        st.markdown("### 📁 Carpetas Ignoradas")
        st.info("""
        Las siguientes carpetas se ignorarán automáticamente:
        - `.git`, `.svn`
        - `node_modules`
        - `__pycache__`
        - `.vscode`, `.idea`
        - `venv`, `env`
        """)
        
        st.markdown("### 🔍 Vista Previa")
        if 'folder_report' in st.session_state:
            with st.expander("Estructura de carpeta"):
                st.json(st.session_state['folder_report']['folder_info']['tree_structure'])

# Tab 3: Fuentes Markdown
with tab3:
    st.header("Ingesta de Fuentes Bibliográficas")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Selector de método de entrada
        input_method = st.radio(
            "Método de entrada",
            ["Escribir/Pegar Markdown", "Cargar archivo .md", "Usar plantilla"],
            horizontal=True
        )
        
        markdown_content = ""
        
        if input_method == "Escribir/Pegar Markdown":
            markdown_content = st.text_area(
                "Contenido Markdown",
                height=400,
                placeholder="""Pega aquí tu documento con fuentes estructuradas...

**ID:** [SRC-001]
**Tipo:** Documento Académico
**Título:** ...""",
                help="Cada fuente debe seguir el formato estructurado especificado"
            )
        
        elif input_method == "Cargar archivo .md":
            md_file = st.file_uploader(
                "Selecciona archivo Markdown",
                type=['md', 'markdown', 'txt'],
                key="md_uploader"
            )
            
            if md_file:
                markdown_content = md_file.read().decode('utf-8')
                st.success(f"✅ Archivo cargado: {md_file.name}")
                
                # Vista previa
                with st.expander("Vista previa del contenido"):
                    st.text(markdown_content[:1000] + "..." if len(markdown_content) > 1000 else markdown_content)
        
        else:  # Usar plantilla
            language = st.selectbox("Idioma de la plantilla", ["Español", "English"])
            lang_code = 'es' if language == "Español" else 'en'
            
            if st.button("📄 Generar Plantilla"):
                async def get_template():
                    template = await ingestion_system.markdown_parser.generate_template(lang_code)
                    return template
                
                template = asyncio.run(get_template())
                markdown_content = template
                st.session_state['markdown_template'] = template
            
            if 'markdown_template' in st.session_state:
                markdown_content = st.text_area(
                    "Plantilla (editable)",
                    value=st.session_state['markdown_template'],
                    height=400,
                    help="Modifica la plantilla con tus propias fuentes"
                )
        
        # Validación y procesamiento
        if markdown_content:
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✔️ Validar Formato", use_container_width=True):
                    async def validate():
                        result = await ingestion_system.markdown_parser.validate_source_format(
                            markdown_content
                        )
                        return result
                    
                    validation = asyncio.run(validate())
                    
                    if validation['valid']:
                        st.success(f"✅ Formato válido: {validation['source_count']} fuentes encontradas")
                    else:
                        st.error("❌ Formato inválido")
                        for error in validation['errors']:
                            st.error(f"• {error}")
                    
                    if validation['warnings']:
                        for warning in validation['warnings']:
                            st.warning(f"⚠️ {warning}")
            
            with col_btn2:
                if st.button("🚀 Procesar Fuentes", type="primary", use_container_width=True):
                    with st.spinner("Procesando fuentes bibliográficas..."):
                        async def process_sources():
                            job = await ingestion_system.ingest_markdown_sources(
                                markdown_content=markdown_content,
                                user_id=st.session_state.get('user_id', 'default'),
                                source_name=f"sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )
                            return job
                        
                        job = asyncio.run(process_sources())
                        
                        if job.status == IngestionStatus.COMPLETED:
                            st.balloons()
                            st.success(f"✅ {job.processed_files} fuentes procesadas exitosamente")
                        else:
                            st.error(f"Error procesando fuentes: {job.status.value}")
    
    with col2:
        st.markdown("### 📖 Formato Requerido")
        st.code("""
**ID:** [SRC-XXX]
**Tipo:** [Tipo]
**Título:** [Título]
**Autor(es):** [Autores]
**Editorial/Origen:** [Editorial]
**Año:** [Año]
**URL/DOI:** [URL]
**Citación:** [Cita]
**Documento_Fuente:** [Doc]
        """, language="markdown")
        
        st.markdown("### 📌 Tipos Comunes")
        st.info("""
        • Documento Académico
        • Libro
        • Herramienta de Software
        • Sitio Web
        • Conferencia
        • Documentación
        """)

# Tab 4: Repositorios de GitHub
with tab4:
    st.header("🐙 Ingesta de Repositorios GitHub")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Información del Repositorio")
        
        # Input para URL del repositorio
        repo_url = st.text_input(
            "URL del Repositorio GitHub",
            placeholder="https://github.com/usuario/repositorio",
            help="Introduce la URL de un repositorio público de GitHub"
        )
        
        # Opciones avanzadas
        with st.expander("⚙️ Opciones Avanzadas"):
            branch = st.text_input(
                "Rama (Branch)",
                value="main",
                help="Rama a clonar (por defecto: main)"
            )
            
            include_docs = st.checkbox(
                "Incluir solo documentación",
                value=False,
                help="Procesar solo archivos README, docs, y similares"
            )
            
            include_code = st.checkbox(
                "Incluir código fuente",
                value=True,
                help="Procesar archivos de código fuente"
            )
            
            max_file_size_mb = st.slider(
                "Tamaño máximo de archivo (MB)",
                min_value=1,
                max_value=200,
                value=50,
                help="Ignorar archivos más grandes que este tamaño"
            )
            
            exclude_patterns = st.text_area(
                "Patrones de exclusión (uno por línea)",
                value="*.min.js\n*.min.css\ntest_*\n*_test.*",
                help="Archivos que coincidan con estos patrones serán ignorados"
            )
        
        if repo_url:
            # Validar URL de GitHub
            if "github.com" in repo_url:
                # Extraer información del repositorio
                try:
                    parts = repo_url.replace("https://", "").replace("http://", "").split("/")
                    if len(parts) >= 3:
                        owner = parts[1]
                        repo = parts[2].replace(".git", "")
                        
                        st.success(f"✅ Repositorio detectado: **{owner}/{repo}**")
                        
                        # Botón para analizar repositorio
                        if st.button("🔍 Analizar Repositorio", use_container_width=True):
                            with st.spinner("Analizando repositorio..."):
                                async def analyze_repo():
                                    analyzer = GitHubProcessor()
                                    analysis = await analyzer.analyze_repository(
                                        owner=owner,
                                        repo=repo,
                                        branch=branch
                                    )
                                    return analysis
                                
                                analysis = asyncio.run(analyze_repo())
                                st.session_state['repo_analysis'] = analysis
                                
                                # Mostrar análisis
                                st.success("✅ Análisis completado")
                        
                        # Mostrar análisis si existe
                        if 'repo_analysis' in st.session_state:
                            analysis = st.session_state['repo_analysis']
                            
                            # Métricas del repositorio
                            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                            
                            with col_m1:
                                st.metric("⭐ Estrellas", analysis.get('stars', 0))
                            with col_m2:
                                st.metric("🍴 Forks", analysis.get('forks', 0))
                            with col_m3:
                                st.metric("📄 Archivos", analysis.get('file_count', 0))
                            with col_m4:
                                st.metric("💾 Tamaño", f"{analysis.get('size_mb', 0):.1f} MB")
                            
                            # Estructura del repositorio
                            st.markdown("### 📂 Estructura del Repositorio")
                            
                            # Mostrar archivos importantes
                            if analysis.get('important_files'):
                                st.markdown("**Archivos Principales:**")
                                for file in analysis['important_files']:
                                    st.markdown(f"• `{file}`")
                            
                            # Lenguajes detectados
                            if analysis.get('languages'):
                                st.markdown("**Lenguajes Detectados:**")
                                lang_df = pd.DataFrame([
                                    {"Lenguaje": lang, "Porcentaje": pct}
                                    for lang, pct in analysis['languages'].items()
                                ])
                                
                                fig = px.pie(
                                    lang_df,
                                    values='Porcentaje',
                                    names='Lenguaje',
                                    title='Distribución de Lenguajes'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Botón de procesamiento
                            if st.button("🚀 Procesar Repositorio", type="primary", use_container_width=True):
                                with st.spinner(f"Clonando y procesando repositorio {owner}/{repo}..."):
                                    async def process_repo():
                                        job = await ingestion_system.ingest_github_repository(
                                            repo_url=repo_url,
                                            branch=branch,
                                            user_id=st.session_state.get('user_id', 'default'),
                                            options={
                                                'include_docs': include_docs,
                                                'include_code': include_code,
                                                'max_file_size_mb': max_file_size_mb,
                                                'exclude_patterns': exclude_patterns.split('\n')
                                            }
                                        )
                                        return job
                                    
                                    job = asyncio.run(process_repo())
                                    
                                    if job.status == IngestionStatus.COMPLETED:
                                        st.balloons()
                                        st.success(f"""
                                        ✅ **Repositorio procesado exitosamente**
                                        - Archivos procesados: {job.processed_files}
                                        - Tiempo total: {(job.end_time - job.start_time).total_seconds():.2f}s
                                        """)
                                    else:
                                        st.error(f"Error procesando repositorio: {job.status.value}")
                else:
                    st.error("URL de GitHub inválida")
            else:
                st.warning("Por favor, introduce una URL válida de GitHub")
    
    with col2:
        st.markdown("### 🐙 Acerca de GitHub")
        st.info("""
        **Limitaciones:**
        - Solo repositorios públicos
        - Máximo 500MB por repositorio
        - Se respetan los rate limits de GitHub
        
        **Archivos procesados:**
        - README y documentación
        - Código fuente
        - Configuración
        - Notebooks Jupyter
        """)
        
        st.markdown("### 💡 Ejemplos de Repositorios")
        example_repos = [
            "https://github.com/langchain-ai/langchain",
            "https://github.com/streamlit/streamlit",
            "https://github.com/ollama/ollama"
        ]
        
        for repo in example_repos:
            if st.button(f"📎 {repo.split('/')[-1]}", key=repo):
                st.session_state['repo_url_example'] = repo
                st.rerun()

# Tab 5: Monitor de Trabajos
with tab5:
    st.header("📊 Monitor de Trabajos")
    
    # Obtener trabajos del usuario
    user_jobs = ingestion_system.get_user_jobs(
        st.session_state.get('user_id', 'default')
    )
    
    if user_jobs:
        # Filtros
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            status_filter = st.selectbox(
                "Filtrar por estado",
                ["Todos"] + [s.value for s in IngestionStatus]
            )
        
        with col_f2:
            type_filter = st.selectbox(
                "Filtrar por tipo",
                ["Todos", "file", "folder", "markdown_sources", "github_repository"]
            )
        
        with col_f3:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        
        # Filtrar trabajos
        filtered_jobs = user_jobs
        if status_filter != "Todos":
            filtered_jobs = [j for j in filtered_jobs if j.status.value == status_filter]
        if type_filter != "Todos":
            filtered_jobs = [j for j in filtered_jobs if j.type == type_filter]
        
        # Mostrar trabajos
        for job in filtered_jobs[:10]:  # Mostrar últimos 10
            with st.expander(f"Job {job.job_id[:8]}... - {job.type}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Badge de estado
                    status_class = {
                        IngestionStatus.PENDING: "status-pending",
                        IngestionStatus.PROCESSING: "status-processing",
                        IngestionStatus.COMPLETED: "status-completed",
                        IngestionStatus.FAILED: "status-failed",
                        IngestionStatus.PARTIALLY_COMPLETED: "status-partially"
                    }.get(job.status, "status-pending")
                    
                    st.markdown(
                        f'<span class="job-status-badge {status_class}">{job.status.value}</span>',
                        unsafe_allow_html=True
                    )
                
                with col2:
                    st.metric("Archivos", f"{job.processed_files}/{job.total_files}")
                
                with col3:
                    duration = (job.end_time or datetime.now()) - job.start_time
                    st.metric("Duración", f"{duration.total_seconds():.1f}s")
                
                # Barra de progreso
                if job.total_files > 0:
                    progress = job.processed_files / job.total_files
                    st.progress(progress)
                
                # Detalles
                if job.errors:
                    st.error(f"Errores: {len(job.errors)}")
                    for error in job.errors[:3]:
                        st.text(f"• {error}")
                
                # Acciones
                if job.status in [IngestionStatus.PENDING, IngestionStatus.PROCESSING]:
                    if st.button(f"❌ Cancelar", key=f"cancel_{job.job_id}"):
                        asyncio.run(ingestion_system.cancel_job(job.job_id))
                        st.rerun()
    else:
        st.info("No hay trabajos para mostrar")

# Tab 6: Estadísticas
with tab6:
    st.header("📈 Estadísticas del Sistema")
    
    stats = ingestion_system.get_statistics()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Trabajos", stats['total_jobs'])
    with col2:
        st.metric("Completados", stats['completed_jobs'], 
                 delta=f"{(stats['completed_jobs']/stats['total_jobs']*100):.0f}%" if stats['total_jobs'] > 0 else "0%")
    with col3:
        st.metric("En Proceso", stats['processing_jobs'])
    with col4:
        st.metric("Tasa de Éxito", f"{stats['success_rate']:.1f}%")
    
    # Gráficos
    if stats['total_files'] > 0:
        # Gráfico de dona para estado de archivos
        fig = go.Figure(data=[go.Pie(
            labels=['Procesados', 'Fallidos', 'Pendientes'],
            values=[
                stats['processed_files'],
                stats['failed_files'],
                stats['total_files'] - stats['processed_files'] - stats['failed_files']
            ],
            hole=.3
        )])
        
        fig.update_layout(title="Estado de Archivos")
        st.plotly_chart(fig, use_container_width=True)

# Sidebar con información adicional
with st.sidebar:
    st.markdown("### 📌 Guía Rápida")
    st.markdown("""
    1. **Archivos**: Arrastra o selecciona archivos
    2. **Carpetas**: Introduce la ruta completa
    3. **Markdown**: Pega o carga fuentes estructuradas
    4. **GitHub**: Introduce URL del repositorio
    5. **Monitor**: Revisa el estado de los trabajos
    """)
    
    st.markdown("### 🔧 Configuración")
    
    # Configuración del usuario
    user_id = st.text_input(
        "ID de Usuario",
        value=st.session_state.get('user_id', 'default'),
        help="Identificador único para tus trabajos"
    )
    
    if user_id != st.session_state.get('user_id'):
        st.session_state['user_id'] = user_id
        st.success("ID de usuario actualizado")
    
    st.markdown("### 📊 Resumen")
    stats = ingestion_system.get_statistics()
    st.info(f"""
    **Archivos procesados hoy:** {stats['processed_files']}
    **Trabajos activos:** {stats['processing_jobs']}
    **Tasa de éxito:** {stats['success_rate']:.1f}%
    """)
```

## 5. Procesador de GitHub

### `app/ingestion/github_processor.py`

```python
"""
Procesador para Repositorios de GitHub
Clona y procesa repositorios públicos de GitHub
"""

import os
import shutil
import tempfile
import asyncio
import aiohttp
import git
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import fnmatch

from app.common.logger import Logger

logger = Logger(__name__)

class GitHubProcessor:
    """
    Procesador especializado para repositorios de GitHub
    """
    
    def __init__(self):
        """Inicializa el procesador de GitHub"""
        self.github_api_base = "https://api.github.com"
        self.max_repo_size_mb = 500
        self.default_branch = "main"
        
        # Archivos importantes a buscar
        self.important_files = [
            'README.md', 'README.rst', 'README.txt',
            'LICENSE', 'LICENSE.md', 'LICENSE.txt',
            'CONTRIBUTING.md', 'CONTRIBUTING.rst',
            'CHANGELOG.md', 'CHANGELOG.rst',
            'requirements.txt', 'package.json', 'pom.xml',
            'setup.py', 'setup.cfg', 'pyproject.toml',
            'Dockerfile', 'docker-compose.yml',
            '.gitignore', '.env.example'
        ]
        
        # Patrones de archivos a ignorar por defecto
        self.default_ignore_patterns = [
            '*.pyc', '*.pyo', '__pycache__',
            '*.class', '*.jar', '*.war',
            '*.exe', '*.dll', '*.so', '*.dylib',
            '*.log', '*.tmp', '*.temp',
            '.git', '.svn', '.hg',
            'node_modules', 'vendor', 'venv', 'env',
            '*.min.js', '*.min.css',
            'dist', 'build', 'target',
            '*.sqlite', '*.db',
            '*.jpg', '*.jpeg', '*.png', '*.gif', '*.ico',
            '*.mp3', '*.mp4', '*.avi', '*.mov'
        ]
        
        logger.info("Procesador de GitHub inicializado")
    
    async def analyze_repository(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza un repositorio de GitHub sin clonarlo
        
        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            branch: Rama a analizar
            
        Returns:
            Análisis del repositorio
        """
        analysis = {
            'owner': owner,
            'repo': repo,
            'branch': branch or self.default_branch,
            'valid': False,
            'error': None
        }
        
        try:
            # Obtener información del repositorio via API
            async with aiohttp.ClientSession() as session:
                # Información básica del repo
                repo_url = f"{self.github_api_base}/repos/{owner}/{repo}"
                async with session.get(repo_url) as response:
                    if response.status == 200:
                        repo_data = await response.json()
                        
                        analysis.update({
                            'valid': True,
                            'name': repo_data['name'],
                            'full_name': repo_data['full_name'],
                            'description': repo_data['description'],
                            'stars': repo_data['stargazers_count'],
                            'forks': repo_data['forks_count'],
                            'size_kb': repo_data['size'],
                            'size_mb': repo_data['size'] / 1024,
                            'default_branch': repo_data['default_branch'],
                            'language': repo_data['language'],
                            'created_at': repo_data['created_at'],
                            'updated_at': repo_data['updated_at'],
                            'topics': repo_data.get('topics', [])
                        })
                        
                        # Verificar tamaño
                        if analysis['size_mb'] > self.max_repo_size_mb:
                            analysis['error'] = f"Repositorio muy grande ({analysis['size_mb']:.1f} MB)"
                            analysis['valid'] = False
                            return analysis
                        
                    else:
                        analysis['error'] = f"Repositorio no encontrado o privado (HTTP {response.status})"
                        return analysis
                
                # Obtener lenguajes
                languages_url = f"{self.github_api_base}/repos/{owner}/{repo}/languages"
                async with session.get(languages_url) as response:
                    if response.status == 200:
                        languages = await response.json()
                        total_bytes = sum(languages.values())
                        
                        if total_bytes > 0:
                            analysis['languages'] = {
                                lang: round(bytes_count / total_bytes * 100, 1)
                                for lang, bytes_count in languages.items()
                            }
                
                # Obtener estructura del repositorio (primer nivel)
                contents_url = f"{self.github_api_base}/repos/{owner}/{repo}/contents"
                async with session.get(contents_url) as response:
                    if response.status == 200:
                        contents = await response.json()
                        
                        analysis['file_count'] = sum(1 for item in contents if item['type'] == 'file')
                        analysis['dir_count'] = sum(1 for item in contents if item['type'] == 'dir')
                        
                        # Buscar archivos importantes
                        important_found = []
                        for item in contents:
                            if item['name'] in self.important_files:
                                important_found.append(item['name'])
                        
                        analysis['important_files'] = important_found
                        
                        # Estructura básica
                        analysis['structure'] = {
                            'files': [item['name'] for item in contents if item['type'] == 'file'][:20],
                            'directories': [item['name'] for item in contents if item['type'] == 'dir'][:20]
                        }
                
                # Obtener README si existe
                readme_url = f"{self.github_api_base}/repos/{owner}/{repo}/readme"
                async with session.get(readme_url) as response:
                    if response.status == 200:
                        readme_data = await response.json()
                        analysis['has_readme'] = True
                        analysis['readme_size'] = readme_data.get('size', 0)
                    else:
                        analysis['has_readme'] = False
                
        except Exception as e:
            logger.error(f"Error analizando repositorio {owner}/{repo}: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    async def clone_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        depth: int = 1
    ) -> Optional[str]:
        """
        Clona un repositorio de GitHub
        
        Args:
            repo_url: URL del repositorio
            branch: Rama a clonar
            depth: Profundidad del clone (1 para shallow clone)
            
        Returns:
            Ruta temporal del repositorio clonado
        """
        temp_dir = None
        
        try:
            # Crear directorio temporal
            temp_dir = tempfile.mkdtemp(prefix="github_repo_")
            logger.info(f"Clonando repositorio en: {temp_dir}")
            
            # Configurar opciones de clonado
            clone_options = ['--depth', str(depth)]
            if branch:
                clone_options.extend(['--branch', branch])
            
            # Clonar repositorio
            repo = git.Repo.clone_from(
                repo_url,
                temp_dir,
                multi_options=clone_options
            )
            
            logger.info(f"Repositorio clonado exitosamente: {repo_url}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"Error clonando repositorio: {e}")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    
    async def process_repository(
        self,
        repo_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa un repositorio clonado
        
        Args:
            repo_path: Ruta del repositorio clonado
            options: Opciones de procesamiento
            
        Returns:
            Resumen del procesamiento
        """
        result = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'errors': [],
            'file_types': {},
            'total_size': 0
        }
        
        try:
            repo_path = Path(repo_path)
            
            # Obtener patrones de exclusión
            exclude_patterns = options.get('exclude_patterns', []) + self.default_ignore_patterns
            max_file_size = options.get('max_file_size_mb', 50) * 1024 * 1024
            include_docs_only = options.get('include_docs', False)
            include_code = options.get('include_code', True)
            
            # Recorrer archivos del repositorio
            for file_path in repo_path.rglob('*'):
                if file_path.is_file():
                    result['total_files'] += 1
                    
                    # Verificar si debe ser excluido
                    should_skip = False
                    relative_path = str(file_path.relative_to(repo_path))
                    
                    # Verificar patrones de exclusión
                    for pattern in exclude_patterns:
                        if fnmatch.fnmatch(relative_path, pattern) or \
                           fnmatch.fnmatch(file_path.name, pattern):
                            should_skip = True
                            break
                    
                    if should_skip:
                        result['skipped_files'] += 1
                        continue
                    
                    # Verificar tamaño
                    file_size = file_path.stat().st_size
                    if file_size > max_file_size:
                        result['skipped_files'] += 1
                        logger.debug(f"Archivo muy grande ignorado: {file_path.name}")
                        continue
                    
                    # Verificar tipo de archivo
                    file_ext = file_path.suffix.lower()
                    
                    # Si solo documentación
                    if include_docs_only:
                        doc_extensions = ['.md', '.rst', '.txt', '.pdf', '.docx']
                        doc_names = ['readme', 'license', 'contributing', 'changelog', 'todo']
                        
                        is_doc = (file_ext in doc_extensions or 
                                 any(name in file_path.name.lower() for name in doc_names))
                        
                        if not is_doc:
                            result['skipped_files'] += 1
                            continue
                    
                    # Si no incluir código
                    if not include_code:
                        code_extensions = [
                            '.py', '.js', '.java', '.cpp', '.c', '.cs', '.go',
                            '.rs', '.kt', '.swift', '.rb', '.php', '.scala'
                        ]
                        if file_ext in code_extensions:
                            result['skipped_files'] += 1
                            continue
                    
                    # Procesar archivo
                    result['processed_files'] += 1
                    result['total_size'] += file_size
                    
                    # Estadísticas por tipo
                    if file_ext:
                        result['file_types'][file_ext] = result['file_types'].get(file_ext, 0) + 1
                    
            # Crear resumen
            result['summary'] = {
                'files_by_type': sorted(
                    result['file_types'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                'total_size_mb': result['total_size'] / (1024 * 1024),
                'avg_file_size_kb': (result['total_size'] / result['processed_files'] / 1024) 
                                   if result['processed_files'] > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error procesando repositorio: {e}")
            result['errors'].append(str(e))
        
        return result
    
    async def extract_repository_files(
        self,
        repo_path: str,
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extrae archivos procesables del repositorio
        
        Args:
            repo_path: Ruta del repositorio
            options: Opciones de extracción
            
        Returns:
            Lista de archivos extraídos con metadata
        """
        files = []
        repo_path = Path(repo_path)
        
        # Obtener información del repositorio git
        try:
            repo = git.Repo(repo_path)
            repo_info = {
                'remote_url': repo.remotes.origin.url if repo.remotes else None,
                'branch': repo.active_branch.name if not repo.head.is_detached else 'detached',
                'commit': repo.head.commit.hexsha[:8]
            }
        except:
            repo_info = {}
        
        # Procesar archivos según el resultado del procesamiento
        process_result = await self.process_repository(repo_path, options)
        
        # Extraer archivos válidos
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(repo_path))
                
                # Crear metadata del archivo
                file_info = {
                    'path': str(file_path),
                    'relative_path': relative_path,
                    'name': file_path.name,
                    'extension': file_path.suffix.lower(),
                    'size': file_path.stat().st_size,
                    'repo_info': repo_info,
                    'metadata': {
                        'source': 'github',
                        'repository': repo_info.get('remote_url', 'unknown'),
                        'branch': repo_info.get('branch', 'unknown'),
                        'commit': repo_info.get('commit', 'unknown'),
                        'file_path': relative_path
                    }
                }
                
                files.append(file_info)
        
        return files
    
    async def cleanup_repository(self, repo_path: str) -> bool:
        """
        Limpia el repositorio temporal
        
        Args:
            repo_path: Ruta del repositorio a limpiar
            
        Returns:
            True si se limpió exitosamente
        """
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info(f"Repositorio temporal limpiado: {repo_path}")
                return True
        except Exception as e:
            logger.error(f"Error limpiando repositorio: {e}")
        
        return False
```

## 6. Actualización del Sistema Principal

### Actualizar `app/ingestion/advanced_ingestion_system.py`

Añade este método a la clase `AdvancedIngestionSystem`:

```python
    async def ingest_github_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        user_id: str = "default",
        options: Optional[Dict[str, Any]] = None
    ) -> IngestionJob:
        """
        Procesa un repositorio público de GitHub
        
        Args:
            repo_url: URL del repositorio de GitHub
            branch: Rama a procesar (opcional)
            user_id: ID del usuario
            options: Opciones de procesamiento
            
        Returns:
            IngestionJob con el estado del proceso
        """
        job_id = self._generate_job_id(user_id)
        job = IngestionJob(
            job_id=job_id,
            type='github_repository',
            metadata={
                'repo_url': repo_url,
                'branch': branch,
                'options': options or {}
            }
        )
        
        self.active_jobs[job_id] = job
        github_processor = GitHubProcessor()
        temp_repo_path = None
        
        try:
            job.status = IngestionStatus.VALIDATING
            
            # Extraer información del repositorio
            parts = repo_url.replace("https://", "").replace("http://", "").split("/")
            if len(parts) < 3:
                raise ValueError("URL de repositorio inválida")
            
            owner = parts[1]
            repo_name = parts[2].replace(".git", "")
            
            # Analizar repositorio
            logger.info(f"Analizando repositorio: {owner}/{repo_name}")
            analysis = await github_processor.analyze_repository(
                owner=owner,
                repo=repo_name,
                branch=branch
            )
            
            if not analysis['valid']:
                raise ValueError(f"Repositorio inválido: {analysis.get('error', 'Unknown error')}")
            
            if analysis['size_mb'] > 500:
                raise ValueError(f"Repositorio muy grande: {analysis['size_mb']:.1f} MB (máximo 500 MB)")
            
            # Clonar repositorio
            job.status = IngestionStatus.PROCESSING
            logger.info(f"Clonando repositorio: {repo_url}")
            
            temp_repo_path = await github_processor.clone_repository(
                repo_url=repo_url,
                branch=branch or analysis.get('default_branch', 'main'),
                depth=1  # Shallow clone para optimizar
            )
            
            if not temp_repo_path:
                raise ValueError("No se pudo clonar el repositorio")
            
            # Extraer archivos del repositorio
            logger.info("Extrayendo archivos del repositorio")
            repo_files = await github_processor.extract_repository_files(
                repo_path=temp_repo_path,
                options=options or {}
            )
            
            job.total_files = len(repo_files)
            logger.info(f"Encontrados {job.total_files} archivos para procesar")
            
            # Procesar archivos del repositorio
            for file_info in repo_files:
                try:
                    # Verificar tamaño
                    if file_info['size'] > self.max_file_size:
                        job.errors.append({
                            'file': file_info['relative_path'],
                            'error': f"Archivo muy grande: {file_info['size'] / 1024 / 1024:.1f} MB"
                        })
                        job.failed_files += 1
                        continue
                    
                    # Verificar extensión
                    file_extension = file_info['extension']
                    if not any(file_extension in exts for exts in self.supported_formats.values()):
                        job.failed_files += 1
                        continue
                    
                    # Leer contenido del archivo
                    with open(file_info['path'], 'rb') as f:
                        file_content = f.read()
                    
                    # Crear wrapper para el archivo
                    class FileWrapper:
                        def __init__(self, content, name, metadata):
                            self.content = content
                            self.name = name
                            self.metadata = metadata
                            
                        def read(self):
                            return self.content
                    
                    wrapped_file = FileWrapper(
                        file_content,
                        file_info['name'],
                        file_info['metadata']
                    )
                    
                    # Procesar archivo
                    validation_result = {
                        'valid': True,
                        'extension': file_extension,
                        'category': self._get_category_for_extension(file_extension),
                        'size': file_info['size']
                    }
                    
                    result = await self._process_single_file(
                        wrapped_file,
                        user_id,
                        validation_result
                    )
                    
                    # Añadir metadata del repositorio
                    result['repo_metadata'] = file_info['metadata']
                    
                    job.files.append(result)
                    job.processed_files += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando archivo {file_info['name']}: {e}")
                    job.errors.append({
                        'file': file_info['relative_path'],
                        'error': str(e)
                    })
                    job.failed_files += 1
            
            # Determinar estado final
            if job.processed_files == job.total_files:
                job.status = IngestionStatus.COMPLETED
            elif job.processed_files > 0:
                job.status = IngestionStatus.PARTIALLY_COMPLETED
            else:
                job.status = IngestionStatus.FAILED
            
            logger.info(f"Procesamiento de repositorio completado: {job.processed_files}/{job.total_files} archivos")
            
        except Exception as e:
            logger.error(f"Error en ingesta de repositorio GitHub: {e}")
            job.status = IngestionStatus.FAILED
            job.errors.append({
                'general': str(e)
            })
        
        finally:
            # Limpiar repositorio temporal
            if temp_repo_path:
                await github_processor.cleanup_repository(temp_repo_path)
            
            job.end_time = datetime.now()
        
        return job
    
    def _get_category_for_extension(self, extension: str) -> str:
        """Obtiene la categoría para una extensión de archivo"""
        for category, extensions in self.supported_formats.items():
            if extension in extensions:
                return category
        return 'other'
```

## 7. Requirements Actualizados

### `requirements.txt`

Añade estas dependencias:

```txt
# Procesamiento de GitHub
GitPython>=3.1.40
aiohttp>=3.9.0
fnmatch2>=0.4.0
```

## 8. Ejemplo de Uso

```python
# Ejemplo de uso del sistema completo
import asyncio
from app.ingestion.advanced_ingestion_system import AdvancedIngestionSystem

async def main():
    system = AdvancedIngestionSystem()
    
    # 1. Procesar archivos individuales
    files = [...]  # Lista de archivos
    job1 = await system.ingest_files(files, user_id="user123")
    
    # 2. Procesar carpeta
    job2 = await system.ingest_folder(
        "/path/to/folder",
        user_id="user123",
        recursive=True
    )
    
    # 3. Procesar fuentes markdown
    markdown = """
    **ID:** [SRC-001]
    **Tipo:** Libro
    **Título:** Deep Learning
    ...
    """
    job3 = await system.ingest_markdown_sources(
        markdown,
        user_id="user123"
    )
    
    # 4. Procesar repositorio GitHub
    job4 = await system.ingest_github_repository(
        "https://github.com/langchain-ai/langchain",
        branch="main",
        user_id="user123",
        options={
            'include_docs': True,
            'include_code': True,
            'max_file_size_mb': 50
        }
    )
    
    # Verificar estado
    print(f"GitHub Job Status: {job4.status}")
    print(f"Processed: {job4.processed_files}/{job4.total_files}")

if __name__ == "__main__":
    asyncio.run(main())
```

Este sistema de ingesta avanzado ahora incluye:

1. **Soporte completo para GitHub**: Clonación, análisis y procesamiento de repositorios públicos
2. **Análisis previo**: Verificación del tamaño, estructura y contenido antes de clonar
3. **Filtrado inteligente**: Exclusión de archivos binarios, dependencias, y archivos no relevantes
4. **Metadata enriquecida**: Información del repositorio, commit, branch, etc.
5. **Limpieza automática**: Eliminación de archivos temporales después del procesamiento
6. **Interfaz completa**: Tab dedicada en Streamlit para repositorios de GitHub
7. **Seguridad**: Solo repositorios públicos, límites de tamaño, validación de URLs

El sistema es completamente asíncrono y escalable, con manejo robusto de errores y una interfaz de usuario intuitiva para todos los tipos de ingesta.