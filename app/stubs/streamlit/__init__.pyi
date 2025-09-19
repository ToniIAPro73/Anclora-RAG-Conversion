"""
Streamlit stub file for Pylance.
This file helps Pylance understand the structure of the streamlit module.
"""
from typing import Optional, Dict, Any, List, Callable, Union, Iterator, ContextManager

__version__: str = "1.49.1"

def set_page_config(
    page_title: Optional[str] = None,
    page_icon: Optional[str] = None,
    layout: Optional[str] = None,
    initial_sidebar_state: Optional[str] = None,
    menu_items: Optional[Dict[str, Any]] = None
) -> None:
    """Configure the Streamlit page."""
    pass

def title(text: str) -> None:
    """Display text in title formatting."""
    pass

def markdown(body: str) -> None:
    """Display string formatted as Markdown."""
    pass

class ChatMessage:
    """Chat message context manager."""
    def __enter__(self) -> 'ChatMessage':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

def chat_input(placeholder: Optional[str] = None) -> Optional[str]:
    """Display a chat input widget."""
    pass

def chat_message(name: str) -> ChatMessage:
    """Display a chat message."""
    return ChatMessage()

class SessionState:
    """Session state class."""
    def __init__(self):
        self._dict = {}
    
    def __contains__(self, key: str) -> bool:
        return key in self._dict
    
    def __getattr__(self, name: str) -> Any:
        if name in self._dict:
            return self._dict[name]
        self._dict[name] = None
        return None
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_dict":
            super().__setattr__(name, value)
        else:
            self._dict[name] = value

# This is the session state that's accessed as st.session_state
session_state: SessionState = SessionState()