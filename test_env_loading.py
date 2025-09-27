#!/usr/bin/env python3
"""
Script de prueba para verificar que las variables de entorno se carguen correctamente
"""

import os
import sys

# Agregar el directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Archivo .env cargado correctamente")
except ImportError:
    print("[ERROR] python-dotenv no esta instalado")
    sys.exit(1)

# Verificar tokens criticos
print("\n[INFO] Verificando tokens de API:")
api_token = os.getenv('ANCLORA_API_TOKEN')
default_token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')

if api_token:
    print(f"[OK] ANCLORA_API_TOKEN: {api_token[:20]}...")
else:
    print("[ERROR] ANCLORA_API_TOKEN: No encontrado")

if default_token:
    print(f"[OK] ANCLORA_DEFAULT_API_TOKEN: {default_token}")
else:
    print("[ERROR] ANCLORA_DEFAULT_API_TOKEN: No encontrado")

# Verificar configuracion de servicios
print("\n[INFO] Verificando configuracion de servicios:")
chroma_host = os.getenv('CHROMA_HOST', 'No configurado')
ollama_host = os.getenv('OLLAMA_HOST', 'No configurado')
print(f"CHROMA_HOST: {chroma_host}")
print(f"OLLAMA_HOST: {ollama_host}")

# Probar la funcion de carga de API settings (simulada)
def test_api_settings():
    """Simular la funcion _load_api_settings de la aplicacion"""
    token = os.getenv('ANCLORA_API_TOKEN')
    if not token:
        tokens_value = os.getenv('ANCLORA_API_TOKENS')
        if tokens_value:
            token_candidates = [tok.strip() for tok in tokens_value.replace(';', ',').split(',') if tok.strip()]
            if token_candidates:
                token = token_candidates[0]
    if not token:
        token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')

    return {
        'token': token or '',
        'chat_url': 'http://localhost:8081/chat',
        'timeout': '60',
    }

print("\n[INFO] Probando configuracion de API:")
settings = test_api_settings()
if settings['token']:
    print(f"[OK] Token de API encontrado: {settings['token'][:20]}...")
    print(f"[OK] Chat URL: {settings['chat_url']}")
    print("[OK] Configuracion de API valida")
else:
    print("[ERROR] No se pudo encontrar un token de API valido")
    print("[INFO] Buscando en todas las variables ANCLORA:")
    for key, value in os.environ.items():
        if 'ANCLORA' in key:
            print(f"  {key}: {value[:50]}...")