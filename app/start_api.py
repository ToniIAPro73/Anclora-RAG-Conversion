#!/usr/bin/env python3
"""Script de inicio para el servicio API de Anclora RAG."""

import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Función principal para iniciar el servicio API."""
    try:
        # Asegurar que el directorio actual está en el PYTHONPATH
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        logger.info(f"Directorio actual: {current_dir}")
        logger.info(f"PYTHONPATH: {sys.path[:3]}")
        
        # Verificar que el directorio common existe
        common_dir = os.path.join(current_dir, 'common')
        if not os.path.exists(common_dir):
            logger.error(f"✗ Directorio common no encontrado en: {common_dir}")
            sys.exit(1)
        
        logger.info(f"✓ Directorio common encontrado: {common_dir}")
        
        # Verificar que los módulos necesarios están disponibles
        try:
            import common.langchain_module
            logger.info("✓ Módulos common.langchain_module importado correctamente")
        except ImportError as e:
            logger.error(f"✗ Error importando common.langchain_module: {e}")
            # Intentar importar otros módulos para diagnóstico
            try:
                import common
                logger.info("✓ Módulo common base importado")
                logger.info(f"Contenido de common: {dir(common)}")
                
                # Intentar importar módulos específicos para diagnóstico
                try:
                    import common.config
                    logger.info("✓ common.config importado")
                except ImportError as e3:
                    logger.error(f"✗ Error importando common.config: {e3}")
                
                # Listar archivos en el directorio common
                common_files = os.listdir(common_dir)
                logger.info(f"Archivos en common: {common_files}")
                
            except ImportError as e2:
                logger.error(f"✗ Error importando common base: {e2}")
            
            # No salir inmediatamente, intentar continuar sin langchain_module
            logger.warning("Continuando sin common.langchain_module...")
        
        # Importar y ejecutar la API
        logger.info("Iniciando servidor API...")
        import api_endpoints
        import uvicorn
        
        # Configuración del servidor
        config = {
            "host": "0.0.0.0",
            "port": 8081,
            "log_level": "info",
            "access_log": True,
            "reload": False
        }
        
        logger.info(f"Servidor API iniciándose en {config['host']}:{config['port']}")
        uvicorn.run(api_endpoints.app, **config)
        
    except Exception as e:
        logger.error(f"Error iniciando el servidor API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()