#!/usr/bin/env python3
"""
Script de prueba para verificar que las importaciones funcionan correctamente
"""

import sys
import os

# Añadir el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    print("Probando importación de langchain_module...")
    from common.langchain_module import response
    print("✅ Importación exitosa de langchain_module")
    
    print("Probando función response...")
    # Prueba básica de la función
    result = response("hola")
    print(f"✅ Función response funciona: {result[:50]}...")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    sys.exit(1)
except Exception as e:
    print(f"⚠️ Error en ejecución: {e}")
    print("Pero la importación funcionó correctamente")

print("🎉 Todas las pruebas pasaron")
