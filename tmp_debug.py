import sys, os, io, traceback
sys.path.insert(0, os.getcwd())
from app.common import ingest_file as ingest_module

records = []

class _DummyStreamlit:
    def __getattr__(self, name):
        def _call(*args, **kwargs):
            pass
        return _call

ingest_module.st = _DummyStreamlit()

class FakeCollection:
    def __init__(self, name):
        self.name = name
        self.docs = []
    def add_records(self, documents):
        self.docs.extend(documents)
    def get(self, include=None, where=None):
        return {'ids': [], 'metadatas': [], 'documents': []}
    def delete(self, ids=None):
        return None

class FakeClient:
    def __init__(self):
        self.collections = {}
    def get_or_create_collection(self, name):
        if name not in self.collections:
            self.collections[name] = FakeCollection(name)
        return self.collections[name]

ingest_module.CHROMA_SETTINGS = FakeClient()

orig_load = ingest_module._load_documents

def debug_load(uploaded_file, file_name):
    try:
        docs, ing = orig_load(uploaded_file, file_name)
        print('loaded', [type(d) for d in docs])
        return docs, ing
    except Exception as e:
        print('load failed type', type(e), e)
        traceback.print_exc()
        raise

ingest_module._load_documents = debug_load

uploaded = io.BytesIO(b'Contenido de prueba')
uploaded.name = 'manual.txt'
uploaded.size = len(uploaded.getvalue())

try:
    result = ingest_module.ingest_file(uploaded, uploaded.name)
    print('result', result)
except Exception as e:
    print('ingest exception', e)
finally:
    ingest_module._load_documents = orig_load
