import logging
from rich.console import Console
from typing import Optional

class ErrorHandler:
    def __init__(self, console: Console):
        self.console = console
        
        # Nastavení loggeru
        self.logger = logging.getLogger('ytbai')
        self.logger.setLevel(logging.INFO)
        
        # Handler pro soubor
        fh = logging.FileHandler('ytbai.log')
        fh.setLevel(logging.INFO)
        
        # Handler pro konzoli
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        
        # Formát logů
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Přidání handlerů
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    # Základní metody pro logování
    def debug(self, msg, *args, **kwargs):
        """Debug log"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Info log"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Warning log"""
        self.logger.warning(msg, *args, **kwargs)
        self.console.print(f"[yellow]{msg}[/yellow]")

    def error(self, msg, *args, **kwargs):
        """Error log"""
        self.logger.error(msg, *args, **kwargs)
        self.console.print(f"[red]{msg}[/red]")

    def critical(self, msg, *args, **kwargs):
        """Critical log"""
        self.logger.critical(msg, *args, **kwargs)
        self.console.print(f"[red bold]{msg}[/red bold]")

    # Původní metody
    def handle_error(self, error: Exception, context: str = "") -> None:
        """Centrální zpracování chyb"""
        try:
            self.console.print(f"[red]Neočekávaná chyba v {context}: {error}[/red]")
            self.logger.error(f"Unexpected error in {context}: {error}", exc_info=True)
        except Exception as e:
            print(f"Kritická chyba při zpracování chyby: {e}")

    def log_info(self, message: str) -> None:
        """Logování informační zprávy"""
        self.info(message)

    def log_warning(self, message: str) -> None:
        """Logování varování"""
        self.warning(message)

    def log_error(self, message: str, exc_info: bool = False) -> None:
        """Logování chyby"""
        self.error(message, exc_info=exc_info)

    def log_debug(self, message: str) -> None:
        """Logování debug informace"""
        self.debug(message)