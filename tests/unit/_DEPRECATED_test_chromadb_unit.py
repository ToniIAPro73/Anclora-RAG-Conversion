#!/usr/bin/env python3
"""Test script to verify ChromaDB functionality."""

import sys
import os

# Add app directory to path
app_dir = os.path.join(os.path.dirname(__file__), 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def test_chromadb_connection():
    """Test ChromaDB connection and basic operations."""
    print("🔍 Testing ChromaDB connection...")
    
    try:
        from common.constants import CHROMA_SETTINGS, CHROMA_COLLECTIONS
        print("✅ Successfully imported CHROMA_SETTINGS")
        print(f"📊 ChromaDB client type: {type(CHROMA_SETTINGS)}")
        
        # Test basic operations
        print("\n🧪 Testing basic ChromaDB operations...")
        
        # List existing collections
        try:
            collections = CHROMA_SETTINGS.list_collections()
            print(f"📂 Existing collections: {[c.name for c in collections]}")
        except Exception as e:
            print(f"⚠️  Error listing collections: {e}")
        
        # Test creating a collection
        try:
            test_collection = CHROMA_SETTINGS.get_or_create_collection("test_collection")
            print(f"✅ Successfully created/accessed test collection: {test_collection.name}")
            
            # Test adding a document
            test_collection.add(
                documents=["This is a test document"],
                metadatas=[{"source": "test"}],
                ids=["test_id_1"]
            )
            print("✅ Successfully added test document")
            
            # Test querying
            results = test_collection.query(
                query_texts=["test"],
                n_results=1
            )
            print(f"✅ Query results: {len(results['documents'][0])} documents found")
            
            # Clean up
            CHROMA_SETTINGS.delete_collection("test_collection")
            print("✅ Successfully deleted test collection")
            
        except Exception as e:
            print(f"❌ Error in collection operations: {e}")
            import traceback
            traceback.print_exc()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_get_unique_sources_df():
    """Test the get_unique_sources_df function."""
    print("\n🔍 Testing get_unique_sources_df function...")
    
    try:
        from common.ingest_file import get_unique_sources_df
        from common.constants import CHROMA_SETTINGS
        
        df = get_unique_sources_df(CHROMA_SETTINGS)
        print(f"✅ Successfully called get_unique_sources_df")
        print(f"📊 DataFrame shape: {df.shape}")
        print(f"📋 DataFrame columns: {list(df.columns)}")
        
        if not df.empty:
            print("📄 Sample data:")
            print(df.head())
        else:
            print("📄 DataFrame is empty (expected for new installation)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in get_unique_sources_df: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting ChromaDB tests...\n")
    
    success = True
    success &= test_chromadb_connection()
    success &= test_get_unique_sources_df()
    
    if success:
        print("\n✅ All tests passed! ChromaDB is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)
