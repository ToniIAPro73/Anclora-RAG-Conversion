#!/usr/bin/env python3
"""
Anclora RAG Application Runner

This script:
1. Checks for existing Streamlit sessions on port 8501 and kills them
2. Activates the virtual environment if not already active
3. Runs the Streamlit application

Usage: python run_app.py
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use on the system."""
    try:
        # Try to connect to the port
        result = subprocess.run(
            ['netstat', '-an'],
            capture_output=True,
            text=True,
            check=True
        )

        # Check if port 8501 is in use
        return f":{port} " in result.stdout or f":{port}\n" in result.stdout

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: try to find streamlit processes
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq streamlit.exe'],
                capture_output=True,
                text=True,
                check=True
            )
            return 'streamlit.exe' in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def kill_processes_on_port(port: int) -> None:
    """Kill any processes running on the specified port."""
    try:
        # Find processes using the port
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            check=True
        )

        for line in result.stdout.split('\n'):
            if f":{port} " in line and 'LISTENING' in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        print(f"Killing process {pid} on port {port}")
                        subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
                        time.sleep(1)  # Wait a moment for the process to die
                    except subprocess.CalledProcessError:
                        print(f"Failed to kill process {pid}")

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: kill streamlit processes
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'streamlit.exe'], check=True)
            time.sleep(1)
        except subprocess.CalledProcessError:
            pass


def is_venv_active() -> bool:
    """Check if we're in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def activate_virtual_environment() -> None:
    """Activate the virtual environment."""
    venv_path = Path("venv_rag")
    if not venv_path.exists():
        print("Virtual environment 'venv_rag' not found. Please create it first.")
        print("You can create it by running: python -m venv venv_rag")
        sys.exit(1)

    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        if activate_script.exists():
            # For Windows, we need to run the activate script in a new shell
            abs_activate = str(activate_script.resolve())
            print(f"Activating virtual environment: {abs_activate}")
            print("Please activate the virtual environment manually by running:")
            print(f"  {abs_activate}")
            print("Then run this script again.")
            sys.exit(1)
        else:
            print("Virtual environment activation script not found.")
            sys.exit(1)
    else:  # Unix-like systems
        activate_script = venv_path / "bin" / "activate"
        if activate_script.exists():
            abs_activate = str(activate_script.resolve())
            print(f"Activating virtual environment: {abs_activate}")
            print("Please activate the virtual environment manually by running:")
            print(f"  source {abs_activate}")
            print("Then run this script again.")
            sys.exit(1)
        else:
            print("Virtual environment activation script not found.")
            sys.exit(1)


def run_streamlit_app() -> None:
    """Run the Streamlit application."""
    app_path = Path("app") / "Inicio.py"
    if not app_path.exists():
        print(f"Application file not found: {app_path}")
        sys.exit(1)

    print(f"Starting Streamlit application: {app_path}")
    print("Press Ctrl+C to stop the application")

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.headless", "true",
            "--server.port", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run Streamlit application: {e}")
        sys.exit(1)


def main() -> None:
    """Main function to run the application."""
    print("=== Anclora RAG Application Runner ===")

    # Check and kill existing processes on port 8501
    if is_port_in_use(8501):
        print("Found existing processes on port 8501. Killing them...")
        kill_processes_on_port(8501)
        print("Existing processes killed.")
    else:
        print("No existing processes found on port 8501.")

    # Check if virtual environment is active
    if not is_venv_active():
        print("Virtual environment not active. Activating...")
        activate_virtual_environment()
        # Re-check if activation worked
        if not is_venv_active():
            print("Failed to activate virtual environment. Please activate it manually.")
            sys.exit(1)
    else:
        print("Virtual environment is already active.")

    print("Starting application...")
    run_streamlit_app()


if __name__ == "__main__":
    main()