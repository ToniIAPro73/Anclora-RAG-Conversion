try:
    import streamlit
    print("Streamlit import successful!")
    print(f"Streamlit version: {streamlit.__version__}")
except ImportError as e:
    print(f"Failed to import streamlit: {e}")
    
# Also try to import other packages to check environment
try:
    import sys
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
except Exception as e:
    print(f"Error getting Python info: {e}")