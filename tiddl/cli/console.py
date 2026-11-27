from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "text": "grey70",
        "dim_text": "grey42",
        "success": "green",
        "info": "bright_cyan",
        "dim_info": "cyan",
        "warning": "yellow",
        "danger": "bold red",
    }
)

console = Console(theme=custom_theme)
