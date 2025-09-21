"""
Cliente Python para que agentes IA accedan al sistema Anclora RAG
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

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
    def _ensure_utf8(response: requests.Response) -> None:
        if not response.encoding:
            response.encoding = response.apparent_encoding or 'utf-8'

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
            self._ensure_utf8(response)
            return response.json()
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
            max_length (int): Longitud máxima del mensaje
            language (Optional[str]): Idioma a utilizar en la consulta

        Returns:
            Dict con la respuesta del RAG
        """
        try:
            self._ensure_authenticated()

            payload = {
                "message": message,
                "max_length": max_length
            }
            self._add_language_to_payload(payload, language)

            response = self.session.post(f"{self.base_url}/chat", json=payload)
            response.raise_for_status()

            self._ensure_utf8(response)
            result = response.json()
            self.logger.info(f"Consulta exitosa: {message[:50]}...")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en consulta: {e}")
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
            file_path = Path(file_path)
            if not file_path.exists():
                return {"status": "error", "message": "Archivo no encontrado"}

            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
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

            self._ensure_utf8(response)
            result = response.json()
            self.logger.info(f"Documento subido: {file_path.name}")
            return result
            
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
            self._ensure_utf8(response)
            return response.json()
            
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

            self._ensure_utf8(response)
            result = response.json()
            self.logger.info(f"Documento eliminado: {filename}")
            return result
            
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
    
    def add_knowledge(self, file_path: str) -> bool:
        """
        Agregar conocimiento al RAG
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            bool: True si fue exitoso
        """
        result = self.client.upload_document(file_path)
        return result.get("status") == "success"
    
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
