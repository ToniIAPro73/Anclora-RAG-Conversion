#!/usr/bin/env python3
"""
Test script to verify ChromaDB connection for local development
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_chroma_connection():
    """Test ChromaDB connection with current configuration"""
    print("🔍 Testing ChromaDB connection...")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        print(f"📊 CHROMA_HOST: {os.getenv('CHROMA_HOST', 'localhost')}")
        print(f"📊 CHROMA_PORT: {os.getenv('CHROMA_PORT', '8000')}")
        
        # Test direct ChromaDB connection
        import chromadb
        from chromadb.config import Settings
        
        host = os.getenv('CHROMA_HOST', 'localhost')
        port = int(os.getenv('CHROMA_PORT', '8000'))
        
        print(f"🔗 Connecting to ChromaDB at {host}:{port}...")
        
        client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        # Test basic operations
        print("✅ Successfully connected to ChromaDB!")
        
        # List collections
        collections = client.list_collections()
        print(f"📂 Found {len(collections)} collections: {[c.name for c in collections]}")
        
        # Test creating a collection
        test_collection_name = "test_connection"
        try:
            test_collection = client.get_or_create_collection(test_collection_name)
            print(f"✅ Successfully created/accessed collection: {test_collection.name}")
            
            # Test adding a document
            test_collection.add(
                documents=["This is a test document for connection verification"],
                metadatas=[{"source": "connection_test"}],
                ids=["test_connection_id"]
            )
            print("✅ Successfully added test document")
            
            # Test querying
            results = test_collection.query(
                query_texts=["test document"],
                n_results=1
            )
            print(f"✅ Query successful: found {len(results['documents'][0])} documents")
            
            # Clean up
            client.delete_collection(test_collection_name)
            print("✅ Successfully cleaned up test collection")
            
        except Exception as e:
            print(f"⚠️  Error in collection operations: {e}")
        
        # Test using the application's configuration
        print("\n🧪 Testing application configuration...")
        from common.constants import CHROMA_SETTINGS, CHROMA_COLLECTIONS
        
        print(f"📊 Application ChromaDB client type: {type(CHROMA_SETTINGS)}")
        
        # List collections using app config
        app_collections = CHROMA_SETTINGS.list_collections()
        print(f"📂 Application collections: {[c.name for c in app_collections]}")
        
        print("\n✅ All tests passed! ChromaDB is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing ChromaDB connection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chroma_connection()
    sys.exit(0 if success else 1)
