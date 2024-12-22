import os
import sys
from pathlib import Path

# Přidáme kořenový adresář projektu do PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import logging
from rich.console import Console
from src.utils.error_handler import ErrorHandler

# Nastavení loggingu - změněno na INFO level
logging.basicConfig(
    level=logging.INFO,  # Změněno z DEBUG na INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ytbai.log'),
    ]
)

logger = logging.getLogger('ytbai.main')

from src.ui.main_ui import UI
from src.manager.ytbai_manager import YTBAIManager

def main():
    try:
        logger.info("Spouštím aplikaci")
        console = Console()
        manager = YTBAIManager()
        manager.initialize(console)
        ui = UI(manager, console)
        ui.start()
    except Exception as e:
        logger.error(f"Kritická chyba: {e}", exc_info=True)
        return 1
    finally:
        logger.info("Ukončuji aplikaci")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 