"""
Script to install type stubs for streamlit.
"""
import subprocess
import sys

def install_stubs():
    """Install type stubs for streamlit."""
    print("Installing type stubs for streamlit...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "types-streamlit"])
        print("Successfully installed type stubs for streamlit.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install type stubs: {e}")

if __name__ == "__main__":
    install_stubs()