import os, tempfile, uuid
import streamlit as st
import pandas as pd
import logging
from typing import List

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from langchain_community.document_loaders import (
    CSVLoader,
    EverNoteLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredEmailLoader,
    UnstructuredEPubLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredODTLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from common.chroma_db_settings import Chroma
from common.constants import CHROMA_SETTINGS


# Load environment variables
source_directory = os.environ.get('SOURCE_DIRECTORY', 'documents')
embeddings_model_name = os.environ.get('EMBEDDINGS_MODEL_NAME', 'all-MiniLM-L6-v2')
# Create embeddings
embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
collection_name = 'vectordb'
collection = CHROMA_SETTINGS.get_or_create_collection(name='vectordb')
chunk_size = 500
chunk_overlap = 50

# Custom document loaders
class MyElmLoader(UnstructuredEmailLoader):
    """Wrapper to fallback to text/plain when default does not work"""

    def load(self) -> List[Document]:
        """Wrapper adding fallback for elm without html"""
        try:
            try:
                doc = UnstructuredEmailLoader.load(self)
            except ValueError as e:
                if 'text/html content not found in email' in str(e):
                    # Try plain text
                    self.unstructured_kwargs["content_source"]="text/plain"
                    doc = UnstructuredEmailLoader.load(self)
                else:
                    raise
        except Exception as e:
            # Add file_path to exception message
            raise type(e)(f"{self.file_path}: {e}") from e

        return doc


# Map file extensions to document loaders and their arguments
LOADER_MAPPING = {
    ".csv": (CSVLoader, {}),
    ".doc": (UnstructuredWordDocumentLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".enex": (EverNoteLoader, {}),
    ".eml": (MyElmLoader, {}),
    ".epub": (UnstructuredEPubLoader, {}),
    ".html": (UnstructuredHTMLLoader, {}),
    ".md": (UnstructuredMarkdownLoader, {}),
    ".odt": (UnstructuredODTLoader, {}),
    ".pdf": (PyMuPDFLoader, {}),
    ".ppt": (UnstructuredPowerPointLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"})
}


def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
    """
    Valida el archivo subido por el usuario.

    Args:
        uploaded_file: Archivo subido por Streamlit

    Returns:
        tuple[bool, str]: (es_válido, mensaje)
    """
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    if uploaded_file.size > MAX_FILE_SIZE:
        return False, "Archivo demasiado grande (máximo 10MB)"

    allowed_extensions = ['.csv', '.doc', '.docx', '.enex', '.eml', '.epub',
                         '.html', '.md', '.odt', '.pdf', '.ppt', '.pptx', '.txt']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()

    if file_ext not in allowed_extensions:
        return False, f"Tipo de archivo no soportado: {file_ext}"

    return True, "Válido"


def load_single_document(uploaded_file) -> List[Document]:
    """
    Carga un documento desde un archivo subido.

    Args:
        uploaded_file: Archivo subido por Streamlit

    Returns:
        List[Document]: Lista de documentos procesados

    Raises:
        ValueError: Si el tipo de archivo no es soportado
    """
    try:
        # Validar archivo
        is_valid, message = validate_uploaded_file(uploaded_file)
        if not is_valid:
            raise ValueError(message)

        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext in LOADER_MAPPING:
            # Generar un nombre único para el archivo temporal
            tmp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
            tmp_path = os.path.join(tempfile.gettempdir(), tmp_filename)

            # Guardar temporalmente el archivo cargado con el nombre único
            with open(tmp_path, "wb") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())

            try:
                # Crear una instancia del cargador correspondiente
                loader_class, loader_args = LOADER_MAPPING[ext]
                loader = loader_class(tmp_path, **loader_args)
                logger.info(f"Cargando documento: {uploaded_file.name}")
                return loader.load()
            finally:
                # Eliminar el archivo temporal después de usarlo
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        raise ValueError(f"Tipo de archivo no soportado: '{ext}'")

    except Exception as e:
        logger.error(f"Error al cargar documento {uploaded_file.name}: {str(e)}")
        raise



def get_unique_sources_df(chroma_settings):
    df = pd.DataFrame(chroma_settings.get_collection('vectordb').get(include=['embeddings', 'documents', 'metadatas']))
    
    # Suponiendo que 'df' es tu DataFrame original
    sources = df['metadatas'].apply(lambda x: x.get('source', None)).dropna().unique()

    # Obtener solo el nombre de archivo de cada ruta
    file_names = [source.split('/')[-1] for source in sources]

    # Crear un DataFrame con los nombres de archivo únicos
    unique_sources_df = pd.DataFrame(file_names, columns=['source'])

    # Mostrar el DataFrame con los diferentes valores de 'source'
    return unique_sources_df


# Modificar process_file para recibir el archivo cargado y el nombre
def process_file(uploaded_file, file_name):
    files_in_vectordb = get_unique_sources_df(CHROMA_SETTINGS)['source'].tolist()
    if file_name in files_in_vectordb:
        return None
    else:
        # Convertir los bytes a documentos de texto
        documents = load_single_document(uploaded_file)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        texts = text_splitter.split_documents(documents)
        return texts


def does_vectorstore_exist(settings) -> bool:
    """
    Checks if vectorstore exists
    """
    collection = settings.get_or_create_collection(collection_name)
    return collection


def ingest_file(uploaded_file, file_name):
    """
    Procesa e ingesta un archivo en la base de datos vectorial.

    Args:
        uploaded_file: Archivo subido por Streamlit
        file_name (str): Nombre del archivo
    """
    try:
        logger.info(f"Iniciando ingesta del archivo: {file_name}")

        if does_vectorstore_exist(CHROMA_SETTINGS):
            db = Chroma(embedding_function=embeddings, client=CHROMA_SETTINGS)
            texts = process_file(uploaded_file, file_name)

            if texts is None:
                st.warning('Este archivo ya fue agregado anteriormente.')
                logger.warning(f"Archivo duplicado: {file_name}")
            else:
                with st.spinner(f"Creando embeddings para {file_name}..."):
                    db.add_documents(texts)
                st.success(f"Se agregó el archivo '{file_name}' con éxito.")
                logger.info(f"Archivo procesado exitosamente: {file_name}")
        else:
            # Create and store locally vectorstore
            st.info("Creando nueva base de datos vectorial...")
            texts = process_file(uploaded_file, file_name)

            with st.spinner(f"Creando embeddings. Esto puede tomar algunos minutos..."):
                db = Chroma.from_documents(texts, embeddings, client=CHROMA_SETTINGS)
            st.success(f"Se agregó el archivo '{file_name}' con éxito.")
            logger.info(f"Nueva base de datos creada con archivo: {file_name}")

    except Exception as e:
        error_msg = f"Error al procesar el archivo '{file_name}': {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)


def delete_file_from_vectordb(filename:str):
    new_filename = '/tmp/' + filename
    try:
        collection.delete(where={"source": new_filename})
        print(f'Se eliminó el archivo: {filename} con éxito')
    except:
        print(f'Ocurrió un error al eliminar el archivo {filename}')