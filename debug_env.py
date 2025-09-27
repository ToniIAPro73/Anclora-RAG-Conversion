#!/usr/bin/env python3
"""
Debug simple para verificar carga de .env
"""

import os
from dotenv import load_dotenv

print("=== DEBUG SIMPLE DE .ENV ===")
print(f"Directorio actual: {os.getcwd()}")

# Probar diferentes paths para .env
possible_paths = [
    '.env',  # Directorio actual
    '../.env',  # Directorio padre
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
]

for path in possible_paths:
    print(f"\nProbando path: {path}")
    print(f"Archivo existe: {os.path.exists(path)}")
    if os.path.exists(path):
        try:
            load_dotenv(path)
            print(f"[OK] .env cargado desde: {path}")

            # Verificar variables inmediatamente después
            api_token = os.getenv('ANCLORA_API_TOKEN')
            default_token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')

            print(f"ANCLORA_API_TOKEN: {api_token[:20] + '...' if api_token else 'None'}")
            print(f"ANCLORA_DEFAULT_API_TOKEN: {default_token or 'None'}")

            if api_token or default_token:
                print("[SUCCESS] Tokens encontrados!")
                break
        except Exception as e:
            print(f"[ERROR] Error cargando {path}: {e}")
    else:
        print(f"[INFO] Archivo no existe: {path}")

print("\n=== VARIABLES DE ENTORNO FINAL ===")
print(f"ANCLORA_API_TOKEN: {os.getenv('ANCLORA_API_TOKEN')}")
print(f"ANCLORA_DEFAULT_API_TOKEN: {os.getenv('ANCLORA_DEFAULT_API_TOKEN')}")