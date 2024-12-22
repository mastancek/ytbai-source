from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from typing import Dict, List, Set
from ..manager.ytbai_manager import SearchResult
from ..themes.icons import Icons
from ..themes.default_themes import DefaultThemes
import logging

logger = logging.getLogger(__name__)
fh = logging.FileHandler('ytbai.log')
logger.addHandler(fh)

class UICore:
    def __init__(self, console: Console, config: Dict):
        self.console = console
        self.config = config
        self.theme = DefaultThemes.get_theme(config.get('theme', 'dracula'))
        
    def show_main_menu(self) -> str:
        """Zobrazí hlavní menu"""
        options = [
            f"[green]{Icons.get('SEARCH')} 1.[/green] YouTube vyhledávání",
            f"[cyan]{Icons.get('DOWNLOAD')} 2.[/cyan] AI doporučení hudby",
            f"[blue]{Icons.get('SEARCH')} 3.[/blue] Upřesnit vyhledávání",
            f"[yellow]{Icons.get('CHAT')} 4.[/yellow] Chat s hudebním AI",
            f"[magenta]{Icons.get('SETTINGS')} 5.[/magenta] Správa AI služeb",
            f"[green]{Icons.get('THEME')} 6.[/green] Správa nastavení",
            f"[blue]{Icons.get('MUSIC')} 7.[/blue] Přehrávač hudby",
            f"[cyan]{Icons.get('DOWNLOAD')} 8.[/cyan] Webshare stahování",
            f"[magenta]{Icons.get('SPOTIFY')} 9.[/magenta] Spotify vyhledávání",
            f"[red]{Icons.get('EXIT')} K.[/red] Konec",
            "",  # prázdný řádek pro oddělení
            "[cyan]Vyberte možnost ([white]1-9, K[/white]): [/cyan]"  # výzva s formátováním
        ]
        
        panel = Panel(
            "\n".join(options),
            title=f"{Icons.get('MUSIC')} Hlavní Menu",
            border_style=self.theme.get('border', 'blue')
        )
        
        # Vyčistíme předchozí výstup
        self.console.clear()
        
        # Zobrazíme panel
        self.console.print(panel)
        
        # Zachytíme vstup a zobrazíme ho na stejném řádku
        with self.console.capture() as capture:
            choice = ""
            while not choice:
                key = self.console.input()
                if key.upper() in "123456789K":
                    choice = key
                    self.console.print(f"\r[cyan]Zvoleno: [white]{choice.upper()}[/white][/cyan]")
        
        return choice.upper()

    def display_results(self, results: List[SearchResult], selected_indices: Set[int], downloaded_ids: Set[str]) -> None:
        """Zobrazí výsledky vyhledávání"""
        if not results:
            self.console.print("[yellow]Žádné výsledky k zobrazení[/yellow]")
            return

        self.console.print()
        
        table = Table(show_header=True, border_style=self.theme.get('border'))
        table.add_column("č.", justify="right", style="cyan", width=4)
        table.add_column("Název", style="white")
        table.add_column("Interpret", style="green")
        table.add_column("Délka", style="yellow", width=8)
        table.add_column("Kvalita", style="blue", width=8)
        table.add_column("Formát", style="magenta", width=6)
        table.add_column("Žánr", style="cyan")
        table.add_column("Status", justify="center", width=8)

        for i, result in enumerate(results, 1):
            try:
                # Ošetření dlouhých názvů
                title = result.title[:50] + "..." if len(result.title) > 50 else result.title
                artist = result.artist[:20] + "..." if len(result.artist) > 20 else result.artist
                
                # Žánr/tagy
                if result.genre:
                    genre_info = result.genre
                elif result.tags:
                    genre_info = ", ".join(result.tags[:2])
                else:
                    genre_info = "---"
                
                # Status ikony
                status = ""
                if i-1 in selected_indices:
                    status += f"[{self.theme['accent']}]■[/{self.theme['accent']}] "
                else:
                    status += f"[{self.theme['accent']}]□[/{self.theme['accent']}] "
                    
                if result.video_id in downloaded_ids:
                    status += f"[{self.theme['success']}]✓[/{self.theme['success']}]"
                
                table.add_row(
                    str(i),
                    title,
                    artist,
                    result.duration,
                    result.audio_quality or "N/A",
                    result.audio_format or "N/A",
                    genre_info,
                    status
                )
            except Exception as e:
                logger.error(f"Chyba při zobrazení výsledku {i}: {e}")
                self.console.print(f"[{self.theme['error']}]Chyba při zobrazení výsledku {i}: {e}[/{self.theme['error']}]")

        self.console.print(table) 