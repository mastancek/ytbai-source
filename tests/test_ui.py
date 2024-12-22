import pytest
from pathlib import Path
import sys

# Přidání src do PYTHONPATH pro testy
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.ui.main_ui import UI
from src.manager.ytbai_manager import YTBAIManager
from rich.console import Console

def test_ui_initialization():
    console = Console()
    manager = YTBAIManager()
    ui = UI(manager, console)
    assert ui is not None
    assert ui.manager == manager
    assert ui.console == console