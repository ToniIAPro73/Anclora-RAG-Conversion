# API de Anclora RAG

Este documento describe el flujo de autenticación actualizado y la forma de consumir los endpoints protegidos de la API.

## Autenticación

Los endpoints `/chat`, `/upload`, `/documents` y `/documents/{filename}` utilizan autenticación **Bearer**. La API valida el encabezado `Authorization` siguiendo una de las dos modalidades configurables por variables de entorno:

### Tokens estáticos

Define uno o varios tokens compartidos mediante las variables:

- `ANCLORA_API_TOKENS`: lista separada por comas de tokens válidos.
- `ANCLORA_API_TOKEN`: alternativa para definir un único token.

Ejemplo en una terminal UNIX:

```bash
export ANCLORA_API_TOKENS="mi-token-seguro,otro-token"
```

En Docker Compose los valores se propagan automáticamente a los servicios `api` (ver configuración en `docker-compose.yml` y `docker-compose_sin_gpu.yml`).

### JWT (opcional)

Si deseas emitir tokens firmados, define al menos:

- `ANCLORA_JWT_SECRET`: clave para verificar la firma.
- `ANCLORA_JWT_ALGORITHMS`: algoritmos permitidos (por defecto `HS256`).
- `ANCLORA_JWT_AUDIENCE` y `ANCLORA_JWT_ISSUER`: opcionales para validar `aud` e `iss`.

El paquete `PyJWT` (incluido en `app/requirements.txt`) debe estar disponible para validar los tokens firmados.

Cuando se configura `ANCLORA_JWT_SECRET`, los tokens firmados se validan tras comprobar los tokens estáticos. Un token inválido devuelve `401 Token inválido`; la ausencia de configuración produce `500 Autenticación no configurada`.

## Consumo de la API

Enviar el encabezado `Authorization: Bearer <token>` en cada petición. Ejemplo con `curl`:

```bash
curl \
  -H "Authorization: Bearer mi-token-seguro" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola"}' \
  http://localhost:8081/chat
```

El script `open_rag.sh` (Linux/macOS) y `open_rag.bat` (Windows) cargan variables desde `.env` si existe y abortan cuando no se define un token o secreto JWT. Esto garantiza que el servicio se levante únicamente con autenticación habilitada.

## Buenas prácticas

- Mantén los tokens fuera del control de versiones (`.env`).
- Renueva periódicamente los tokens estáticos o las claves de firma.
- Utiliza HTTPS cuando expongas la API fuera de un entorno controlado.
