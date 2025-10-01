"""
Cliente Python para que agentes IA accedan al sistema Anclora RAG
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import requests

from rag_core.conversion_advisor import ConversionAdvisor, FormatRecommendation

class AncloraRAGClient:
    """
    Cliente para interactuar con el sistema Anclora RAG desde agentes IA.

    El cliente permite configurar el esquema de autenticación, seleccionar el
    idioma preferido para las respuestas y maneja automáticamente respuestas
    con caracteres especiales gracias a la normalización del encoding HTTP.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8081",
        api_key: str = "your-api-key-here",
        *,
        auth_scheme: str = "Bearer",
        default_language: str = "es",
        supported_languages: Optional[List[str]] = None,
    ):
        """
        Inicializar cliente RAG

        Args:
            base_url (str): URL base del sistema RAG
            api_key (str): Clave de API para autenticación
            auth_scheme (str): Esquema de autenticación HTTP (Bearer, Token, etc.)
            default_language (str): Idioma por defecto para las consultas
            supported_languages (Optional[List[str]]): Lista de idiomas permitidos
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

        self.logger = logging.getLogger(__name__)

        self._supported_languages = self._normalize_languages(supported_languages)
        self.language = self._validate_language(default_language)

        self.auth_scheme: Optional[str] = auth_scheme.strip() if auth_scheme is not None else None
        self._auth_token: Optional[str] = None
        self.api_key: Optional[str] = None
        if api_key:
            self.set_auth_token(api_key, auth_scheme=self.auth_scheme)

        self._conversion_advisor = ConversionAdvisor()

    def close(self) -> None:
        """Cerrar la sesión HTTP para liberar recursos."""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        """Soporte para context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cerrar sesión al salir del context manager."""
        self.close()

    @staticmethod
    def _normalize_languages(languages: Optional[List[str]]) -> Optional[List[str]]:
        if languages is None:
            return ["es", "en"]

        cleaned: List[str] = []
        for language in languages:
            if not isinstance(language, str):
                continue
            normalized = language.strip().lower()
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)

        return cleaned or ["es", "en"]

    def _validate_language(self, language: Optional[str]) -> str:
        if not isinstance(language, str):
            raise ValueError("El idioma debe ser una cadena de texto.")

        normalized = language.strip().lower()
        if not normalized:
            raise ValueError("El idioma no puede estar vacío.")

        if self._supported_languages and normalized not in self._supported_languages:
            raise ValueError(
                f"Idioma '{normalized}' no soportado. Idiomas disponibles: {', '.join(self._supported_languages)}"
            )

        return normalized

    def set_language(self, language: str) -> str:
        """Actualizar el idioma por defecto para las consultas."""

        self.language = self._validate_language(language)
        return self.language

    def _validate_token(self, token: str) -> str:
        if not isinstance(token, str):
            raise ValueError("El token de autenticación debe ser una cadena de texto.")

        cleaned = token.strip()
        if not cleaned:
            raise ValueError("El token de autenticación no puede estar vacío.")

        return cleaned

    def set_auth_token(self, token: str, auth_scheme: Optional[str] = None) -> None:
        """Configurar el token de autenticación y el esquema utilizado."""

        cleaned_token = self._validate_token(token)

        if auth_scheme is not None:
            scheme = auth_scheme.strip()
            if not scheme and auth_scheme != "":
                raise ValueError("El esquema de autenticación no puede estar vacío.")
            self.auth_scheme = scheme

        scheme = self.auth_scheme
        if scheme is None:
            scheme = "Bearer"

        header_value = f"{scheme} {cleaned_token}" if scheme else cleaned_token

        self._auth_token = cleaned_token
        self.api_key = cleaned_token
        self.session.headers['Authorization'] = header_value

    def _ensure_authenticated(self) -> None:
        if not self._auth_token:
            raise ValueError("No se ha configurado un token de autenticación válido.")

    @staticmethod
    def _safe_json_loads(response: requests.Response) -> Dict[str, Any]:
        """
        Safely parse JSON response with proper encoding handling.

        Args:
            response: The HTTP response object

        Returns:
            Parsed JSON data as dictionary
        """
        # Use response.text which handles encoding automatically and properly
        return response.json()

    def _add_language_to_payload(self, payload: Dict[str, Any], language: Optional[str]) -> None:
        selected_language = language or self.language
        if selected_language:
            payload['language'] = self._validate_language(selected_language)

    def health_check(self) -> Dict[str, Any]:
        """
        Verificar estado del sistema RAG
        
        Returns:
            Dict con información de salud del sistema
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return self._safe_json_loads(response)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            self.logger.error(f"Error HTTP en health check ({status_code}): {e}")
            return {"status": "error", "message": f"HTTP {status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en health check: {e}")
            return {"status": "error", "message": str(e)}
    
    def query(
        self,
        message: str,
        max_length: int = 1000,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Realizar consulta al sistema RAG

        Args:
            message (str): Pregunta o consulta
            max_length (int): Longitud máxima del mensaje (debe ser > 0)
            language (Optional[str]): Idioma a utilizar en la consulta

        Returns:
            Dict con la respuesta del RAG
        """
        try:
            # Input validation
            if not isinstance(max_length, int) or max_length <= 0:
                raise ValueError("max_length debe ser un entero positivo")

            self._ensure_authenticated()

            payload = {
                "message": message,
                "max_length": max_length
            }
            self._add_language_to_payload(payload, language)

            response = self.session.post(f"{self.base_url}/chat", json=payload)
            response.raise_for_status()

            result = self._safe_json_loads(response)
            self.logger.info(f"Consulta exitosa: {message[:50]}...")
            return result

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            self.logger.error(f"Error HTTP en consulta ({status_code}): {e}")
            return {"status": "error", "message": f"HTTP {status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en consulta: {e}")
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            self.logger.error(f"Error de validación: {e}")
            return {"status": "error", "message": str(e)}
    
    def upload_document(self, file_path: str) -> Dict[str, Any]:
        """
        Subir documento al sistema RAG

        Args:
            file_path (str): Ruta al archivo a subir

        Returns:
            Dict con resultado de la operación
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"status": "error", "message": "Archivo no encontrado"}

            with open(file_path_obj, 'rb') as f:
                files = {'file': (file_path_obj.name, f, 'application/octet-stream')}
                # Remover Content-Type header para multipart
                self._ensure_authenticated()
                auth_header = self.session.headers.get('Authorization')
                headers = {'Authorization': auth_header} if auth_header else {}

                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    headers=headers
                )
                response.raise_for_status()

            result = self._safe_json_loads(response)
            self.logger.info(f"Documento subido: {file_path_obj.name}")
            return result

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            self.logger.error(f"Error HTTP al subir documento ({status_code}): {e}")
            return {"status": "error", "message": f"HTTP {status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al subir documento: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_documents(self) -> Dict[str, Any]:
        """
        Listar documentos en la base de conocimiento
        
        Returns:
            Dict con lista de documentos
        """
        try:
            self._ensure_authenticated()
            response = self.session.get(f"{self.base_url}/documents")
            response.raise_for_status()
            return self._safe_json_loads(response)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            self.logger.error(f"Error HTTP al listar documentos ({status_code}): {e}")
            return {"status": "error", "message": f"HTTP {status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al listar documentos: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Eliminar documento de la base de conocimiento

        Args:
            filename (str): Nombre del archivo a eliminar

        Returns:
            Dict con resultado de la operación
        """
        try:
            self._ensure_authenticated()
            response = self.session.delete(f"{self.base_url}/documents/{filename}")
            response.raise_for_status()

            result = self._safe_json_loads(response)
            self.logger.info(f"Documento eliminado: {filename}")
            return result

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            self.logger.error(f"Error HTTP al eliminar documento ({status_code}): {e}")
            return {"status": "error", "message": f"HTTP {status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al eliminar documento: {e}")
            return {"status": "error", "message": str(e)}
    
    def batch_query(self, messages: List[str], language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Realizar múltiples consultas en lote
        
        Args:
            messages (List[str]): Lista de mensajes/consultas
            language (Optional[str]): Idioma a utilizar para todas las consultas

        Returns:
            Lista de respuestas
        """
        results = []
        for message in messages:
            result = self.query(message, language=language)
            results.append(result)
        return results

    def plan_conversion(
        self,
        *,
        source_format: str,
        intended_use: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FormatRecommendation:
        """Consultar el asesor de conversión para obtener el formato recomendado."""

        return self._conversion_advisor.recommend(source_format, intended_use, metadata)


# Ejemplo de uso para agentes IA
class AIAgentRAGInterface:
    """
    Interfaz simplificada para agentes IA.

    Ofrece helpers para ajustar el token de autenticación y el idioma antes de
    interactuar con el servicio RAG.
    """

    def __init__(
        self,
        rag_url: str = "http://localhost:8081",
        api_key: str = "your-api-key-here",
        *,
        auth_scheme: str = "Bearer",
        default_language: str = "es",
        supported_languages: Optional[List[str]] = None,
    ):
        self.client = AncloraRAGClient(
            rag_url,
            api_key,
            auth_scheme=auth_scheme,
            default_language=default_language,
            supported_languages=supported_languages,
        )
        self.logger = logging.getLogger(__name__)
        self._last_conversion_plan: Optional[FormatRecommendation] = None

    def set_auth_token(self, token: str, auth_scheme: Optional[str] = None) -> None:
        """Actualizar el token de autenticación utilizado por el agente."""

        self.client.set_auth_token(token, auth_scheme=auth_scheme)

    def set_language(self, language: str) -> str:
        """Actualizar el idioma por defecto utilizado por el agente."""

        return self.client.set_language(language)

    def ask_question(self, question: str, language: Optional[str] = None) -> str:
        """
        Hacer una pregunta simple al RAG

        Args:
            question (str): Pregunta
            language (Optional[str]): Idioma de la respuesta

        Returns:
            str: Respuesta del RAG
        """
        result = self.client.query(question, language=language)
        if result.get("status") == "success":
            return result.get("response", "Sin respuesta")
        else:
            return f"Error: {result.get('message', 'Error desconocido')}"
    
    def plan_conversion(
        self,
        *,
        file_path: Optional[str] = None,
        source_format: Optional[str] = None,
        intended_use: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FormatRecommendation:
        """Consultar la recomendación de conversión según reglas y metadatos."""

        if not intended_use or not intended_use.strip():
            raise ValueError("El uso previsto no puede estar vacío.")

        normalized_format = (source_format or "").strip().lower()
        if not normalized_format:
            if not file_path:
                raise ValueError("Debe especificar `file_path` o `source_format` para obtener la recomendación.")
            normalized_format = Path(file_path).suffix.lstrip(".")

        normalized_format = normalized_format or "bin"

        plan = self.client.plan_conversion(
            source_format=normalized_format,
            intended_use=intended_use,
            metadata=metadata,
        )
        self._last_conversion_plan = plan
        return plan

    @property
    def last_conversion_plan(self) -> Optional[FormatRecommendation]:
        """Última recomendación calculada por el asesor de conversión."""

        return self._last_conversion_plan

    def add_knowledge(
        self,
        file_path: str,
        *,
        intended_use: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        allow_non_recommended_format: bool = True,
    ) -> bool:
        """
        Agregar conocimiento al RAG

        Args:
            file_path (str): Ruta al archivo
            intended_use (Optional[str]): Uso previsto que guiará el formato recomendado.
            metadata (Optional[Dict[str, Any]]): Metadatos adicionales para evaluar reglas.
            allow_non_recommended_format (bool): Si ``False`` y el archivo no coincide con la recomendación,
                se genera un error antes de subir el documento.

        Returns:
            bool: True si fue exitoso
        """

        plan: Optional[FormatRecommendation] = None
        if intended_use:
            plan = self.plan_conversion(
                file_path=file_path,
                intended_use=intended_use,
                metadata=metadata,
            )

            extension = Path(file_path).suffix
            if extension and not plan.matches_extension(extension):
                message = (
                    f"El archivo '{file_path}' está en formato '{extension.lstrip('.')}'; "
                    f"se recomienda convertirlo a {plan.profile} ({plan.recommended_format})."
                )
                if allow_non_recommended_format:
                    self.logger.warning(message)
                else:
                    raise ValueError(message)

            for contextual_warning in plan.warnings:
                self.logger.warning(contextual_warning)

        result = self.client.upload_document(file_path)
        success = result.get("status") == "success"

        if success and plan:
            self.logger.info(
                "Documento %s preparado para el uso '%s' siguiendo la recomendación %s.",
                file_path,
                intended_use,
                plan.profile,
            )
        elif not success:
            self.logger.error("Error al agregar conocimiento: %s", result.get("message"))

        return success
    
    def get_available_documents(self) -> List[str]:
        """
        Obtener lista de documentos disponibles
        
        Returns:
            List[str]: Lista de nombres de documentos
        """
        result = self.client.list_documents()
        if result.get("status") == "success":
            return result.get("documents", [])
        return []
    
    def is_healthy(self) -> bool:
        """
        Verificar si el sistema está funcionando
        
        Returns:
            bool: True si está saludable
        """
        health = self.client.health_check()
        return health.get("status") == "healthy"


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    # Crear interfaz para agente IA
    ai_interface = AIAgentRAGInterface()

    # Configurar token y lenguaje si fuese necesario
    ai_interface.set_auth_token("your-api-key-here", auth_scheme="Bearer")
    ai_interface.set_language("es")

    # Verificar salud del sistema
    if ai_interface.is_healthy():
        print("✅ Sistema RAG disponible")

        # Hacer una consulta
        response = ai_interface.ask_question("¿Cuáles son los productos de PBC?", language="es")
        print(f"Respuesta: {response}")

        # Realizar una consulta en inglés
        response_en = ai_interface.ask_question("Which are the PBC products?", language="en")
        print(f"Respuesta (en): {response_en}")

        # Listar documentos
        docs = ai_interface.get_available_documents()
        print(f"Documentos disponibles: {docs}")
        
    else:
        print("❌ Sistema RAG no disponible")
