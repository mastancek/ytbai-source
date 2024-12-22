from typing import Dict, Any

THEMES = {
    "dracula": {
        "primary": "purple",
        "secondary": "blue",
        "accent": "green",
        "error": "red",
        "success": "green",
        "border": "blue",
        "background": "black",
        "text": "white"
    },
    "tokyo-night": {
        "primary": "#7aa2f7",
        "secondary": "#bb9af7",
        "accent": "#7dcfff",
        "error": "#f7768e",
        "success": "#9ece6a",
        "border": "#565f89",
        "background": "#1a1b26",
        "text": "#c0caf5"
    },
    "gruvbox": {
        "primary": "#fe8019",
        "secondary": "#b8bb26",
        "accent": "#83a598",
        "error": "#fb4934",
        "success": "#b8bb26",
        "border": "#928374",
        "background": "#282828",
        "text": "#ebdbb2"
    },
    "catppuccin": {
        "primary": "#f5c2e7",
        "secondary": "#cba6f7",
        "accent": "#89dceb",
        "error": "#f38ba8",
        "success": "#a6e3a1",
        "border": "#6c7086",
        "background": "#1e1e2e",
        "text": "#cdd6f4"
    },
    "monokai": {
        "primary": "#f92672",
        "secondary": "#66d9ef",
        "accent": "#a6e22e",
        "error": "#f92672",
        "success": "#a6e22e",
        "border": "#75715e",
        "background": "#272822",
        "text": "#f8f8f2"
    },
    "nord": {
        "primary": "#88c0d0",
        "secondary": "#81a1c1",
        "accent": "#a3be8c",
        "error": "#bf616a",
        "success": "#a3be8c",
        "border": "#4c566a",
        "background": "#2e3440",
        "text": "#eceff4"
    },
    "solarized": {
        "primary": "#268bd2",
        "secondary": "#2aa198",
        "accent": "#859900",
        "error": "#dc322f",
        "success": "#859900",
        "border": "#586e75",
        "background": "#002b36",
        "text": "#839496"
    }
}

def get_theme(name: str) -> Dict[str, str]:
    """Získá téma podle jména"""
    return THEMES.get(name, THEMES["dracula"])

def get_available_themes() -> list[str]:
    """Vrátí seznam dostupných témat"""
    return list(THEMES.keys()) 