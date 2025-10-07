"""
Streamlit stub file for Pylance.
This file helps Pylance understand the structure of the streamlit module.
"""
from typing import Optional, Dict, Any, List, Callable, Union, Iterator, ContextManager, TypeVar

T = TypeVar('T')

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

    def header(self, text: str) -> None:
        """Display a header in the sidebar."""
        pass

    def subheader(self, text: str) -> None:
        """Display a subheader in the sidebar."""
        pass

    def button(
        self,
        label: str,
        key: Optional[str] = None,
        help: Optional[str] = None,
        on_click: Optional[Callable[[], None]] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        type: str = 'secondary',
        disabled: bool = False,
        use_container_width: bool = False,
    ) -> bool:
        """Display a button in the sidebar."""
        return False

    def checkbox(
        self,
        label: str,
        value: bool = False,
        key: Optional[str] = None,
        help: Optional[str] = None,
        on_change: Optional[Callable[[], None]] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        disabled: bool = False,
        label_visibility: str = 'visible',
    ) -> bool:
        """Display a checkbox in the sidebar."""
        return value

    def multiselect(
        self,
        label: str,
        options: List[Any],
        default: Optional[List[Any]] = None,
        key: Optional[str] = None,
        help: Optional[str] = None,
        on_change: Optional[Callable[[], None]] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        max_selections: Optional[int] = None,
        disabled: bool = False,
        label_visibility: str = 'visible',
    ) -> List[Any]:
        """Display a multiselect widget in the sidebar."""
        return default or []

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
        label_visibility: str = 'visible',
    ) -> Any:
        """Display a selectbox widget in the sidebar."""
        pass

    def expander(self, label: str, expanded: bool = False, key: Optional[str] = None) -> ContextManager[Any]:
        """Return a context manager for an expandable sidebar section."""
        class _SidebarExpander(ContextManager[Any]):
            def __enter__(self) -> Any:
                return self
            def __exit__(self, exc_type, exc, tb) -> None:
                return None
        return _SidebarExpander()

# Sidebar instance - can be used both as an object with methods and as a context manager


class _CacheResource:
    def __call__(self, func: Optional[Callable[..., T]] = None, **kwargs: Any) -> Optional[Callable[..., T]]:
        """Decorator placeholder for cached resources."""
        if func is None:
            def decorator(inner_func: Callable[..., T]) -> Callable[..., T]:
                return inner_func  # type: ignore
            return decorator  # type: ignore
        return func

    def clear(self) -> None:
        """Clear cached resources."""
        return None

cache_resource = _CacheResource()
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

def markdown(body: str, unsafe_allow_html: bool = False) -> None:
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

def cache_data(
    func: Optional[Callable] = None,
    ttl: Optional[Union[int, float]] = None,
    max_entries: Optional[int] = None,
    persist: Optional[bool] = None,
    show_spinner: bool = True,
    hash_funcs: Optional[Dict[type, Callable]] = None,
) -> Callable:
    """Decorator to cache data in Streamlit.

    Args:
        func: The function to cache.
        ttl: Time to live for cached data in seconds.
        max_entries: Maximum number of entries to keep in cache.
        persist: Whether to persist cache across reruns.
        show_spinner: Whether to show spinner while computing.
        hash_funcs: Hash functions for custom types.

    Returns:
        Callable: The decorated function.
    """
    pass

def cache(
    func: Optional[Callable] = None,
    ttl: Optional[Union[int, float]] = None,
    max_entries: Optional[int] = None,
    persist: Optional[bool] = None,
    show_spinner: bool = True,
    hash_funcs: Optional[Dict[type, Callable]] = None,
    suppress_st_warning: bool = False,
) -> Callable:
    """Decorator to cache functions in Streamlit (deprecated, use cache_data instead).

    Args:
        func: The function to cache.
        ttl: Time to live for cached data in seconds.
        max_entries: Maximum number of entries to keep in cache.
        persist: Whether to persist cache across reruns.
        show_spinner: Whether to show spinner while computing.
        hash_funcs: Hash functions for custom types.
        suppress_st_warning: Whether to suppress deprecation warning.

    Returns:
        Callable: The decorated function.
    """
    pass

def plotly_chart(
    figure_or_data: Any,
    use_container_width: bool = False,
    sharing: str = "streamlit",
    theme: Optional[str] = None,
    key: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    """Display an interactive Plotly chart.

    Args:
        figure_or_data: The plotly figure or data to display.
        use_container_width: Whether to use the full container width.
        sharing: Sharing mode for the chart.
        theme: Theme for the chart.
        key: An optional string to use as the unique key for the widget.
        on_change: An optional callback invoked when this chart's value changes.
        args: Optional tuple of args to pass to the callback.
        kwargs: Optional dict of kwargs to pass to the callback.

    Returns:
        Any: The chart object.
    """
    pass

def line_chart(
    data: Any,
    x: Optional[str] = None,
    y: Optional[Union[str, List[str]]] = None,
    width: Optional[Union[int, str]] = None,
    height: Optional[Union[int, str]] = None,
    use_container_width: bool = False,
) -> Any:
    """Display a line chart.

    Args:
        data: Data to be plotted.
        x: Column name to use for x-axis.
        y: Column name(s) to use for y-axis.
        width: Width of the chart.
        height: Height of the chart.
        use_container_width: Whether to use the full container width.

    Returns:
        Any: The chart object.
    """
    pass

def bar_chart(
    data: Any,
    x: Optional[str] = None,
    y: Optional[Union[str, List[str]]] = None,
    width: Optional[Union[int, str]] = None,
    height: Optional[Union[int, str]] = None,
    use_container_width: bool = False,
) -> Any:
    """Display a bar chart.

    Args:
        data: Data to be plotted.
        x: Column name to use for x-axis.
        y: Column name(s) to use for y-axis.
        width: Width of the chart.
        height: Height of the chart.
        use_container_width: Whether to use the full container width.

    Returns:
        Any: The chart object.
    """
    pass

def stop() -> None:
    """Stop execution of the app."""
    pass

def json(body: Any, expanded: bool = True) -> None:
    """Display object or string as a JSON string."""
    pass

def tabs(tabs: List[str]) -> List[Any]:
    """Create tabs for organizing content."""
    pass

def caption(text: str) -> None:
    """Display text in caption formatting."""
    pass

def header(text: str) -> None:
    """Display text in header formatting."""
    pass

def checkbox(
    label: str,
    value: bool = False,
    key: Optional[str] = None,
    help: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> bool:
    """Display a checkbox widget."""
    pass

def text_input(
    label: str,
    value: str = "",
    max_chars: Optional[int] = None,
    key: Optional[str] = None,
    type: str = "default",
    help: Optional[str] = None,
    autocomplete: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    placeholder: Optional[str] = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> str:
    """Display a text input widget."""
    pass

def slider(
    label: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    value: Optional[Union[int, float]] = None,
    step: Optional[Union[int, float]] = None,
    format: Optional[str] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> Union[int, float]:
    """Display a slider widget."""
    pass

def expander(
    label: str,
    expanded: bool = False,
    key: Optional[str] = None,
) -> ContextManager[Any]:
    """Create an expandable container."""
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

def metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
) -> None:
    """Display a metric in big bold font with an optional delta indicator."""
    pass

def code(
    body: str,
    language: Optional[str] = None,
) -> None:
    """Display code with optional syntax highlighting."""
    pass

def download_button(
    label: str,
    data: Any,
    file_name: Optional[str] = None,
    mime: Optional[str] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
    on_change: Optional[Callable[[], None]] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    type: str = "primary",
    disabled: bool = False,
    use_container_width: bool = False,
) -> bool:
    """Display a download button widget."""
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