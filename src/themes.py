from typing import Dict, Any
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from rich.theme import Theme
from rich.console import Console
from exceptions import ConfigError

@dataclass
class ColorScheme:
    """Barevné schéma pro aplikaci"""
    primary: str = "cyan"
    secondary: str = "green"
    accent: str = "yellow"
    error: str = "red"
    warning: str = "yellow"
    success: str = "green"
    info: str = "blue"
    muted: str = "dim"
    background: str = "black"
    text: str = "white"

class ThemeManager:
    """Správce témat aplikace"""
    DEFAULT_THEMES = {
        "default": ColorScheme(),
        "dark": ColorScheme(
            primary="blue",
            secondary="cyan",
            accent="magenta",
            background="black",
            text="white"
        ),
        "doom": ColorScheme(  # Doom Emacs inspired
            primary="#51afef",  # bright-blue
            secondary="#98be65",  # bright-green
            accent="#c678dd",  # bright-purple
            error="#ff6c6b",  # bright-red
            warning="#ECBE7B",  # bright-yellow
            success="#98be65",  # bright-green
            info="#51afef",  # bright-blue
            muted="#5B6268",  # base7
            background="#282c34",  # base2
            text="#bbc2cf"  # base8
        ),
        "gruvbox-dark": ColorScheme(
            primary="#458588",  # bright blue
            secondary="#98971a",  # bright green
            accent="#d79921",  # bright yellow
            error="#cc241d",  # bright red
            warning="#d79921",  # bright yellow
            success="#98971a",  # bright green
            info="#458588",  # bright blue
            muted="#928374",  # gray
            background="#282828",  # bg0
            text="#ebdbb2"  # fg1
        ),
        "gruvbox-light": ColorScheme(
            primary="#076678",  # dark blue
            secondary="#79740e",  # dark green
            accent="#b57614",  # dark yellow
            error="#9d0006",  # dark red
            warning="#b57614",  # dark yellow
            success="#79740e",  # dark green
            info="#076678",  # dark blue
            muted="#928374",  # gray
            background="#fbf1c7",  # bg0
            text="#3c3836"  # fg1
        ),
        "tokyo-night": ColorScheme(
            primary="#7aa2f7",  # blue
            secondary="#9ece6a",  # green
            accent="#bb9af7",  # purple
            error="#f7768e",  # red
            warning="#e0af68",  # yellow
            success="#9ece6a",  # green
            info="#7aa2f7",  # blue
            muted="#565f89",  # comment
            background="#1a1b26",  # bg
            text="#c0caf5"  # fg
        ),
        "tokyo-night-storm": ColorScheme(
            primary="#7aa2f7",
            secondary="#9ece6a",
            accent="#bb9af7",
            error="#f7768e",
            warning="#e0af68",
            success="#9ece6a",
            info="#7aa2f7",
            muted="#565f89",
            background="#24283b",
            text="#c0caf5"
        ),
        "catppuccin-mocha": ColorScheme(  # Dark theme
            primary="#89b4fa",  # Blue
            secondary="#a6e3a1",  # Green
            accent="#f5c2e7",  # Pink
            error="#f38ba8",  # Red
            warning="#f9e2af",  # Yellow
            success="#a6e3a1",  # Green
            info="#89b4fa",  # Blue
            muted="#6c7086",  # Overlay0
            background="#1e1e2e",  # Base
            text="#cdd6f4"  # Text
        ),
        "catppuccin-macchiato": ColorScheme(
            primary="#8aadf4",
            secondary="#a6da95",
            accent="#f5bde6",
            error="#ed8796",
            warning="#eed49f",
            success="#a6da95",
            info="#8aadf4",
            muted="#5b6078",
            background="#24273a",
            text="#cad3f5"
        ),
        "catppuccin-frappe": ColorScheme(
            primary="#8caaee",
            secondary="#a6d189",
            accent="#f4b8e4",
            error="#e78284",
            warning="#e5c890",
            success="#a6d189",
            info="#8caaee",
            muted="#626880",
            background="#303446",
            text="#c6d0f5"
        ),
        "catppuccin-latte": ColorScheme(  # Light theme
            primary="#1e66f5",
            secondary="#40a02b",
            accent="#ea76cb",
            error="#d20f39",
            warning="#df8e1d",
            success="#40a02b",
            info="#1e66f5",
            muted="#9ca0b0",
            background="#eff1f5",
            text="#4c4f69"
        ),
        "monokai": ColorScheme(
            primary="#66d9ef",  # Blue
            secondary="#a6e22e",  # Green
            accent="#fd971f",  # Orange
            error="#f92672",  # Red
            warning="#fd971f",  # Orange
            success="#a6e22e",  # Green
            info="#66d9ef",  # Blue
            muted="#75715e",  # Comment
            background="#272822",  # Background
            text="#f8f8f2"  # Foreground
        ),
        "monokai-pro": ColorScheme(
            primary="#78dce8",  # Blue
            secondary="#a9dc76",  # Green
            accent="#ffd866",  # Yellow
            error="#ff6188",  # Red
            warning="#fc9867",  # Orange
            success="#a9dc76",  # Green
            info="#78dce8",  # Blue
            muted="#727072",  # Comment
            background="#2d2a2e",  # Background
            text="#fcfcfa"  # Foreground
        ),
        # Původní témata ponecháme
        "matrix": ColorScheme(
            primary="green",
            secondary="bright_green",
            accent="white",
            error="red",
            warning="yellow",
            success="green",
            info="cyan",
            muted="dim",
            background="black",
            text="green"
        ),
        "dracula": ColorScheme(
            primary="#bd93f9",  # Purple
            secondary="#ff79c6",  # Pink
            accent="#8be9fd",  # Cyan
            error="#ff5555",  # Red
            warning="#ffb86c",  # Orange
            success="#50fa7b",  # Green
            info="#6272a4",  # Comment
            muted="#6272a4",  # Comment
            background="#282a36",  # Background
            text="#f8f8f2"  # Foreground
        )
    }

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.themes_file = config_dir / "themes.json"
        self.current_theme = "default"
        self.custom_themes: Dict[str, ColorScheme] = {}
        self._load_themes()

    def _load_themes(self) -> None:
        """Načte uložená témata"""
        try:
            if self.themes_file.exists():
                with open(self.themes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_theme = data.get('current_theme', 'default')
                    custom_themes = data.get('custom_themes', {})
                    self.custom_themes = {
                        name: ColorScheme(**theme)
                        for name, theme in custom_themes.items()
                    }
        except Exception as e:
            raise ConfigError(f"Chyba při načítání témat: {str(e)}")

    def _save_themes(self) -> None:
        """Uloží témata do souboru"""
        try:
            data = {
                'current_theme': self.current_theme,
                'custom_themes': {
                    name: asdict(theme)
                    for name, theme in self.custom_themes.items()
                }
            }
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise ConfigError(f"Chyba při ukládání témat: {str(e)}")

    def get_theme(self, name: str = None) -> Dict[str, str]:
        """Získá téma podle jména jako slovník"""
        name = name or self.current_theme
        
        if name in self.custom_themes:
            scheme = self.custom_themes[name]
        elif name in self.DEFAULT_THEMES:
            scheme = self.DEFAULT_THEMES[name]
        else:
            scheme = self.DEFAULT_THEMES["default"]

        return {
            "primary": scheme.primary,
            "secondary": scheme.secondary,
            "accent": scheme.accent,
            "error": scheme.error,
            "warning": scheme.warning,
            "success": scheme.success,
            "info": scheme.info,
            "muted": scheme.muted,
            "text": scheme.text,
            # Speciální styly
            "heading": f"bold {scheme.primary}",
            "link": f"underline {scheme.info}",
            "prompt": f"bold {scheme.accent}",
            "input": scheme.text,
            "progress.percentage": scheme.accent,
            "progress.bar": scheme.primary,
            "progress.download": scheme.secondary,
        }

    def get_rich_theme(self, name: str = None) -> Theme:
        """Získá téma pro rich"""
        theme_dict = self.get_theme(name)
        return Theme(theme_dict)

    def set_theme(self, name: str) -> None:
        """Nastaví aktivní téma"""
        if name not in self.DEFAULT_THEMES and name not in self.custom_themes:
            raise ConfigError(f"Téma '{name}' neexistuje")
            
        self.current_theme = name
        self._save_themes()

    def create_custom_theme(self, name: str, scheme: ColorScheme) -> None:
        """Vytvoří nové vlastní téma"""
        if name in self.DEFAULT_THEMES:
            raise ConfigError(f"Nelze přepsat výchozí téma '{name}'")
            
        self.custom_themes[name] = scheme
        self._save_themes()

    def delete_custom_theme(self, name: str) -> None:
        """Smaže vlastní téma"""
        if name in self.DEFAULT_THEMES:
            raise ConfigError(f"Nelze smazat výchozí téma '{name}'")
            
        if name in self.custom_themes:
            del self.custom_themes[name]
            if self.current_theme == name:
                self.current_theme = "default"
            self._save_themes()

    def list_themes(self) -> Dict[str, str]:
        """Vrátí seznam všech dostupných témat"""
        themes = {
            name: "výchozí" for name in self.DEFAULT_THEMES
        }
        themes.update({
            name: "vlastní" for name in self.custom_themes
        })
        return themes 