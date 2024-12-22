from rich.console import Console
from rich.theme import Theme
from typing import Dict, Any
from .themes import get_theme, get_available_themes
from .theme_downloader import ThemeDownloader
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.status import Status

class ThemeManager:
    def __init__(self, console: Console, config: Dict[str, Any]):
        self.console = console
        self.config = config
        self.current_theme = config.get('theme', 'dracula')
        self._apply_theme(self.current_theme)

    def _apply_theme(self, theme_name: str) -> None:
        """Aplikuje téma na konzoli"""
        theme_colors = get_theme(theme_name)
        rich_theme = Theme(theme_colors)
        
        # Vytvoříme novou konzoli s novým tématem
        new_console = Console(theme=rich_theme)
        
        # Zkopírujeme důležité atributy ze staré konzole
        new_console.width = self.console.width
        new_console.height = self.console.height
        new_console.file = self.console.file
        
        # Nahradíme starou konzoli novou
        self.console = new_console
        
        # Vyčistíme obrazovku pro okamžitý efekt
        self.console.clear()

    def apply_theme(self, theme_name: str) -> None:
        """Změní téma a uloží ho do konfigurace"""
        self._apply_theme(theme_name)
        self.config['theme'] = theme_name
        self.current_theme = theme_name
        
        # Znovu vykreslíme aktuální menu
        if hasattr(self.console, '_live'):
            self.console._live.refresh()

    def get_available_themes(self) -> list[str]:
        """Vrátí seznam dostupných témat"""
        return get_available_themes()

    def download_themes(self):
        """Menu pro stahování témat"""
        downloader = ThemeDownloader()
        
        while True:
            self.console.print("\n[cyan]Stahování témat:[/cyan]")
            
            # Získání dostupných témat
            online_themes = downloader.get_available_online_themes()
            if not online_themes:
                self.console.print("[yellow]Nepodařilo se získat seznam online témat[/yellow]")
                return
            
            # Zobrazení témat
            for i, theme_name in enumerate(online_themes, 1):
                self.console.print(f"{i}. {theme_name}")
            self.console.print("Z. Zpět")
            
            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(online_themes):
                theme_name = list(online_themes.keys())[int(choice)-1]
                
                with Status(f"[cyan]Stahuji téma {theme_name}...[/cyan]"):
                    theme = downloader.download_theme(theme_name)
                    if theme and downloader.save_theme(theme_name, theme):
                        self.console.print(f"[green]Téma {theme_name} staženo[/green]")
                        # Přidání do lokálních témat
                        THEMES[theme_name] = theme
                    else:
                        self.console.print(f"[red]Nepodařilo se stáhnout téma {theme_name}[/red]")