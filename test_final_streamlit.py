#!/usr/bin/env python3
"""
Prueba final que simula exactamente la ejecución de Streamlit
"""

import os
import sys

# Simular el ambiente exacto de Streamlit
print("=== PRUEBA FINAL - SIMULACION DE STREAMLIT ===")

# Cambiar al directorio app (donde Streamlit ejecuta la aplicación)
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
os.chdir(app_dir)
sys.path.insert(0, app_dir)
sys.path.insert(0, os.path.dirname(app_dir))

print(f"Directorio de trabajo simulado: {os.getcwd()}")
print(f"Python path: {sys.path[:2]}")

# Cargar variables de entorno (igual que en la app)
try:
    from dotenv import load_dotenv
    # Buscar .env en el directorio raíz del proyecto (igual que en la app)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
    print(f"[OK] Archivo .env cargado desde: {env_path}")
except Exception as e:
    print(f"[ERROR] Error cargando .env: {e}")
    sys.exit(1)

# Verificar que los tokens estén disponibles
print("\n=== VERIFICACION DE TOKENS ===")
api_token = os.getenv('ANCLORA_API_TOKEN')
default_token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')

print(f"ANCLORA_API_TOKEN: {'Configurado' if api_token else 'No encontrado'}")
print(f"ANCLORA_DEFAULT_API_TOKEN: {'Configurado' if default_token else 'No encontrado'}")

# Simular la función _load_api_settings de la aplicación
def simulate_load_api_settings():
    """Simular exactamente la función _load_api_settings de la app"""
    def _get_env_or_secret(*keys):
        for key in keys:
            env_value = os.getenv(key)
            if env_value and env_value.strip():
                return env_value.strip()
        return None

    token = _get_env_or_secret('api_token', 'API_TOKEN', 'ANCLORA_API_TOKEN')
    if not token:
        tokens_value = _get_env_or_secret('api_tokens', 'ANCLORA_API_TOKENS')
        if tokens_value:
            token_candidates = [tok.strip() for tok in tokens_value.replace(';', ',').split(',') if tok.strip()]
            if token_candidates:
                token = token_candidates[0]
    if not token:
        token = _get_env_or_secret('ANCLORA_DEFAULT_API_TOKEN')

    return {
        'chat_url': 'http://localhost:8081/chat',
        'token': token or '',
        'timeout': '60',
    }

print("\n=== PRUEBA DE _load_api_settings ===")
settings = simulate_load_api_settings()
if settings['token']:
    print(f"[SUCCESS] Token de API encontrado correctamente: {settings['token'][:20]}...")
    print(f"[SUCCESS] Chat URL: {settings['chat_url']}")
    print("[SUCCESS] La aplicacion Streamlit deberia funcionar correctamente")
else:
    print("[ERROR] No se pudo encontrar un token de API valido")
    print("\n[DEBUG] Variables de entorno disponibles:")
    for key, value in os.environ.items():
        if 'ANCLORA' in key:
            print(f"  {key}: {value[:50]}...")