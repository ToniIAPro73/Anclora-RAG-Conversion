import os

# Try to import chromadb, but don't fail if it's not available
try:
    import chromadb
    from chromadb.config import Settings
    chromadb_available = True
except ImportError:
    chromadb = None
    Settings = None
    chromadb_available = False

# Define the folder for storing database
#PERSIST_DIRECTORY = os.environ.get('PERSIST_DIRECTORY', 'db')

# Define the Chroma settings
if chromadb_available and Settings:
    CHROMA_SETTINGS = chromadb.HttpClient(host="host.docker.internal", port=8000, settings=Settings(allow_reset=True, anonymized_telemetry=False))
else:
    CHROMA_SETTINGS = None
