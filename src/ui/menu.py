from rich.console import Console
from rich.panel import Panel

class Menu:
    # Gruvbox barvy
    COLORS = {
        'bg':      '#282828',
        'fg':      '#ebdbb2',
        'red':     '#cc241d',
        'green':   '#98971a',
        'yellow':  '#d79921',
        'blue':    '#458588',
        'purple':  '#b16286',
        'aqua':    '#689d6a',
        'gray':    '#a89984',
        'orange':  '#d65d0e',
    }

    def __init__(self, console: Console):
        self.console = console

    def show_menu(self) -> str:
        """Zobrazí hlavní menu a vrátí volbu uživatele"""
        options = [
            f"[{self.COLORS['green']}]1.[/] YouTube vyhledávání",
            f"[{self.COLORS['aqua']}]2.[/] AI doporučení hudby",
            f"[{self.COLORS['blue']}]3.[/] Upřesnit vyhledávání",
            f"[{self.COLORS['yellow']}]4.[/] Chat s hudebním AI",
            f"[{self.COLORS['purple']}]5.[/] Správa AI služeb",
            f"[{self.COLORS['green']}]6.[/] Správa nastavení",
            f"[{self.COLORS['blue']}]7.[/] Přehrávač hudby",
            f"[{self.COLORS['aqua']}]8.[/] Webshare stahování",
            f"[{self.COLORS['yellow']}]9.[/] Spotify vyhledávání",
            f"[{self.COLORS['red']}]K.[/] Konec",
            "",
            f"[{self.COLORS['gray']}]Vyberte možnost (1-9, K):[/]"
        ]

        panel = Panel(
            "\n".join(options),
            title="[bold]Hlavní Menu[/bold]",
            border_style=self.COLORS['blue']
        )
        
        self.console.print(panel)
        
        choice = input().upper()
        while choice not in "123456789K":
            self.console.print(f"[{self.COLORS['red']}]Neplatná volba. Zadejte znovu:[/]")
            choice = input().upper()
            
        return choice

    def start(self):
        """Spustí hlavní smyčku menu"""
        while True:
            choice = self.show_menu()
            
            if choice == "K":
                self.console.print(f"[{self.COLORS['yellow']}]Program ukončen[/]")
                break
                
            self.console.print(f"[{self.COLORS['green']}]Zvolena možnost: {choice}[/]") 