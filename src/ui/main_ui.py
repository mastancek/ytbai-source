from .core import UICore

class UI:
    def __init__(self, manager, console):
        self.manager = manager
        self.console = console
        self.ui_core = UICore(console, manager.config)
        
    def start(self):
        """Spustí hlavní smyčku aplikace"""
        while True:
            try:
                choice = self.ui_core.show_main_menu()
                
                if choice == 'K':
                    print("Program ukončen uživatelem")
                    break
                    
                print(f"Zvolena možnost: {choice}")
                
            except Exception as e:
                print(f"Chyba: {e}")
                break