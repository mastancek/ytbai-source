from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Dict, Any
import requests

class WebshareDownloader:
    def __init__(self, console: Console, config: Dict[str, Any]):
        self.console = console
        self.config = config
        self.session = requests.Session()
        
    def show_webshare_menu(self):
        """Menu pro Webshare stahování"""
        while True:
            options = [
                "[green]1.[/green] Vyhledat hudbu",
                "[blue]2.[/blue] Stáhnout ze seznamu",
                "[cyan]3.[/green] Nastavení účtu",
                "[red]Z.[/red] Zpět"
            ]
            
            self.console.print(Panel("\n".join(options), title="Webshare stahování"))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                self._search_music()
            elif choice == "2":
                self._download_from_list()
            elif choice == "3":
                self._setup_account() 