from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from typing import Dict, Any, List
from pathlib import Path
import json
from ..themes.icons import Icons

class PlaylistManager:
    def __init__(self, console: Console, config: Dict[str, Any]):
        self.console = console
        self.config = config
        self.playlists_file = Path(config['paths']['cache_dir']) / 'playlists.json'
        self._load_playlists()

    def show_playlist_menu(self):
        """Menu správy playlistů"""
        while True:
            self.console.print("\n[cyan]Správa playlistů:[/cyan]")
            self.console.print("1. Zobrazit playlisty")
            self.console.print("2. Vytvořit playlist")
            self.console.print("3. Upravit playlist")
            self.console.print("4. Smazat playlist")
            self.console.print("5. Importovat playlist")
            self.console.print("6. Exportovat playlist")
            self.console.print("Z. Zpět")

            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice == "1":
                self._show_playlists()
            elif choice == "2":
                self._create_playlist()
            elif choice == "3":
                self._edit_playlist()
            elif choice == "4":
                self._delete_playlist()
            elif choice == "5":
                self._import_playlist()
            elif choice == "6":
                self._export_playlist()

    def _load_playlists(self):
        """Načte playlisty ze souboru"""
        try:
            if self.playlists_file.exists():
                with open(self.playlists_file, 'r', encoding='utf-8') as f:
                    self.playlists = json.load(f)
            else:
                self.playlists = {}
        except Exception as e:
            self.console.print(f"[red]Chyba při načítání playlistů: {e}[/red]")
            self.playlists = {}

    def _save_playlists(self):
        """Uloží playlisty do souboru"""
        try:
            self.playlists_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=2)
        except Exception as e:
            self.console.print(f"[red]Chyba při ukládání playlistů: {e}[/red]")

    def _show_playlists(self):
        """Zobrazí seznam playlistů"""
        if not self.playlists:
            self.console.print("[yellow]Žádné playlisty[/yellow]")
            return

        table = Table(title="Moje playlisty")
        table.add_column("Název")
        table.add_column("Počet skladeb")
        table.add_column("Délka")

        for name, playlist in self.playlists.items():
            table.add_row(
                name,
                str(len(playlist['songs'])),
                self._format_duration(playlist['total_duration'])
            )

        self.console.print(table)

    def _create_playlist(self):
        """Vytvoří nový playlist"""
        name = Prompt.ask("Název playlistu")
        if name in self.playlists:
            self.console.print("[red]Playlist s tímto názvem již existuje[/red]")
            return

        self.playlists[name] = {
            'songs': [],
            'total_duration': 0
        }
        self._save_playlists()
        self.console.print("[green]Playlist vytvořen[/green]")

    def _edit_playlist(self):
        """Upraví existující playlist"""
        if not self.playlists:
            self.console.print("[yellow]Žádné playlisty k úpravě[/yellow]")
            return

        name = Prompt.ask("Název playlistu")
        if name not in self.playlists:
            self.console.print("[red]Playlist nenalezen[/red]")
            return

        # TODO: Implementovat úpravu playlistu

    def _delete_playlist(self):
        """Smaže playlist"""
        if not self.playlists:
            self.console.print("[yellow]Žádné playlisty ke smazání[/yellow]")
            return

        name = Prompt.ask("Název playlistu")
        if name not in self.playlists:
            self.console.print("[red]Playlist nenalezen[/red]")
            return

        if Prompt.ask(f"Opravdu smazat playlist '{name}'?", choices=["ano", "ne"]) == "ano":
            del self.playlists[name]
            self._save_playlists()
            self.console.print("[green]Playlist smazán[/green]")

    def _import_playlist(self):
        """Importuje playlist"""
        # TODO: Implementovat import playlistu

    def _export_playlist(self):
        """Exportuje playlist"""
        # TODO: Implementovat export playlistu

    def _format_duration(self, seconds: int) -> str:
        """Formátuje délku v sekundách na MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"