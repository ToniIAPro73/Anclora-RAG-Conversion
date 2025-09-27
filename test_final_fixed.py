#!/usr/bin/env python3
"""
Prueba final con la implementacion corregida de carga de .env
"""

import os
import sys

# Simular el ambiente exacto de Streamlit
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
os.chdir(app_dir)
sys.path.insert(0, app_dir)
sys.path.insert(0, os.path.dirname(app_dir))

print("=== PRUEBA FINAL CON CARGA CORREGIDA ===")
print(f"Directorio de trabajo: {os.getcwd()}")

# Implementar EXACTAMENTE la misma funcion que en la app
def load_env_file():
    """Cargar variables de entorno desde archivo .env manualmente"""
    try:
        # Intentar múltiples rutas posibles para el .env
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),  # app/../.env
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),  # app/.env
            '.env'  # Directorio actual
        ]

        for env_path in possible_paths:
            print(f"Verificando: {env_path}")
            if os.path.exists(env_path):
                print(f"[OK] Encontrado .env en: {env_path}")
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')

                            # Solo establecer variables ANCLORA para evitar conflictos
                            if key.startswith('ANCLORA'):
                                os.environ[key] = value
                                print(f"  [OK] Variable cargada: {key}")

                return True

        print(f"[WARNING] No se encontró .env en ninguna de las rutas: {possible_paths}")
        return False
    except Exception as e:
        print(f"[ERROR] Error cargando .env manualmente: {e}")
        import traceback
        traceback.print_exc()
        return False

# Cargar .env manualmente (igual que en la app)
if load_env_file():
    print("[OK] Variables de entorno cargadas correctamente")
else:
    print("[ERROR] No se pudo cargar el archivo .env")
    sys.exit(1)

# Verificar que los tokens estén disponibles
print("\n=== VERIFICACION FINAL ===")
api_token = os.getenv('ANCLORA_API_TOKEN')
default_token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')

print(f"ANCLORA_API_TOKEN: {'Configurado' if api_token else 'No encontrado'}")
print(f"ANCLORA_DEFAULT_API_TOKEN: {'Configurado' if default_token else 'No encontrado'}")

if api_token:
    print(f"Valor: {api_token[:20]}...")

if default_token:
    print(f"Valor por defecto: {default_token}")

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
    print(f"[SUCCESS] Token de API encontrado: {settings['token'][:20]}...")
    print(f"[SUCCESS] Chat URL: {settings['chat_url']}")
    print("[SUCCESS] La aplicacion Streamlit deberia funcionar correctamente")
    print("\n[RECOMENDACION] Reinicia la aplicacion Streamlit para aplicar los cambios")
else:
    print("[ERROR] No se pudo encontrar un token de API valido")
    print("\n[SOLUCION] Verifica que el archivo .env tenga el formato correcto:")
    print("  ANCLORA_API_TOKEN=tu_token_aqui")
    print("  ANCLORA_DEFAULT_API_TOKEN=dev-token-local")