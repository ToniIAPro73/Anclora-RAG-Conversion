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

def subheader(text: str) -> None:
    """Display text in subheader formatting."""
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

def file_uploader(
    label: str,
    type: Optional[Union[str, List[str]]] = None,
    accept_multiple_files: bool = False,
    key: Optional[str] = None,
    help: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> Any:
    """Display a file uploader widget."""
    pass

def button(
    label: str,
    key: Optional[str] = None,
    help: Optional[str] = None,
    on_click: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    type: str = "secondary",
    disabled: bool = False,
    use_container_width: bool = False,
) -> bool:
    """Display a button widget."""
    pass

def write(*args, **kwargs) -> None:
    """Write arguments to the app."""
    pass

def data_editor(
    data: Any,
    width: Optional[Union[int, str]] = None,
    height: Optional[Union[int, str]] = None,
    use_container_width: bool = False,
    hide_index: Optional[bool] = None,
    column_order: Optional[List[str]] = None,
    column_config: Optional[Dict[str, Any]] = None,
    num_rows: str = "fixed",
    disabled: bool = False,
    key: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    """Display a data editor widget."""
    pass

def divider() -> None:
    """Display a horizontal divider."""
    pass

def dataframe(
    data: Any,
    width: Optional[Union[int, str]] = None,
    height: Optional[Union[int, str]] = None,
    use_container_width: bool = False,
    hide_index: Optional[bool] = None,
    column_order: Optional[List[str]] = None,
    column_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Display a dataframe."""
    pass

def columns(spec: Union[int, List[Union[int, float]]], gap: Optional[str] = "small") -> List[Any]:
    """Insert columns into the app."""
    pass

def success(body: str, icon: Optional[str] = None) -> None:
    """Display a success message."""
    pass

def rerun() -> None:
    """Rerun the app."""
    pass

def error(body: str, icon: Optional[str] = None) -> None:
    """Display an error message."""
    pass

def warning(body: str, icon: Optional[str] = None) -> None:
    """Display a warning message."""
    pass