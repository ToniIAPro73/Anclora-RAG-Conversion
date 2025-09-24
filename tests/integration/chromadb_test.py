"""
Diagnostic script to verify chromadb installation
"""
import sys
import os
import importlib.util
import pkg_resources

print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("Python path:", sys.path)
print("\n")

# Try to import chromadb
try:
    import chromadb
    print("Successfully imported chromadb")
    print("ChromaDB version:", chromadb.__version__)
    print("ChromaDB package location:", os.path.dirname(chromadb.__file__))
except ImportError as e:
    print("Failed to import chromadb:", e)
    
    # Check if the package is installed
    try:
        chromadb_spec = importlib.util.find_spec("chromadb")
        if chromadb_spec is None:
            print("chromadb package not found in sys.path")
        else:
            print("chromadb package found at:", chromadb_spec.origin)
    except Exception as e:
        print("Error checking for chromadb spec:", e)
    
    # Try to get installed version
    try:
        chromadb_version = pkg_resources.get_distribution("chromadb").version
        print("chromadb is installed with version:", chromadb_version)
    except pkg_resources.DistributionNotFound:
        print("chromadb is not installed according to pkg_resources")
    except Exception as e:
        print("Error checking chromadb version:", e)

print("\n")
print("Installed packages:")
for package in pkg_resources.working_set:
    print(f"{package.key}=={package.version}")