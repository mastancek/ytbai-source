class UICore:
    def __init__(self, console, config):
        self.console = console
        self.config = config
        
    def show_main_menu(self) -> str:
        """Zobrazí hlavní menu"""
        self.console.print("\n=== Hlavní Menu ===")
        self.console.print("1. YouTube vyhledávání")
        self.console.print("2. AI doporučení hudby")
        self.console.print("3. Upřesnit vyhledávání")
        self.console.print("4. Chat s hudebním AI")
        self.console.print("5. Správa AI služeb")
        self.console.print("6. Správa nastavení")
        self.console.print("7. Přehrávač hudby")
        self.console.print("8. Webshare stahování")
        self.console.print("9. Spotify vyhledávání")
        self.console.print("K. Konec")
        self.console.print("=" * 20)
        
        choice = input("Volba: ").upper()
        while choice not in "123456789K":
            choice = input("Neplatná volba. Zadejte znovu: ").upper()
            
        return choice