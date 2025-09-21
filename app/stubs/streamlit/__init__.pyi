"""
Streamlit stub file for Pylance.
This file helps Pylance understand the structure of the streamlit module.
"""
from typing import Optional, Dict, Any, List, Callable, Union, Iterator, ContextManager

__version__: str = "1.49.1"

class Sidebar:
    """Streamlit sidebar context manager."""
    def __enter__(self) -> 'Sidebar':
        """Return self to enable use as a context manager with 'with' statements."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        pass
    
    def title(self, text: str) -> None:
        """Display text in title formatting in the sidebar."""
        pass
    
    def selectbox(
        self,
        label: str,
        options: List[Any],
        index: int = 0,
        format_func: Optional[Callable[[Any], str]] = None,
        key: Optional[str] = None,
        help: Optional[str] = None,
        on_change: Optional[Callable[[], None]] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        disabled: bool = False,
        label_visibility: str = "visible",
    ) -> Any:
        """Display a selectbox widget in the sidebar."""
        pass

# Sidebar instance - can be used both as an object with methods and as a context manager
sidebar: Sidebar = Sidebar()

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

def info(body: str, icon: Optional[str] = None) -> None:
    """Display an informational message."""
    pass

def spinner(text: str) -> ContextManager[None]:
    """Display a spinner while executing a block of code.
    
    Args:
        text (str): The message to display while the spinner is active.
        
    Returns:
        ContextManager: A context manager that displays a spinner when entered and hides it when exited.
    """
    pass

def selectbox(
    label: str,
    options: List[Any],
    index: int = 0,
    format_func: Optional[Callable[[Any], str]] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> Any:
    """Display a selectbox widget.
    
    Args:
        label (str): A short label explaining to the user what this selectbox is for.
        options (List[Any]): A list of options to choose from.
        index (int): The index of the selected option.
        format_func (Callable): Function to format the display of the options.
        key (str): An optional string to use as the unique key for the widget.
        help (str): An optional tooltip that gets displayed next to the selectbox.
        on_change (Callable): An optional callback invoked when this selectbox's value changes.
        args (tuple): Optional tuple of args to pass to the callback.
        kwargs (Dict[str, Any]): Optional dict of kwargs to pass to the callback.
        disabled (bool): An optional boolean, which disables the selectbox if set to True.
        label_visibility (str): The visibility of the label. One of "visible", "hidden", or "collapsed".
        
    Returns:
        Any: The selected option.
    """
    pass