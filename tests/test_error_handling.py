import pytest
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.error_handler import ErrorHandler
from rich.console import Console

def test_error_handler():
    console = Console()
    handler = ErrorHandler(console)
    
    # Test logování chyby
    try:
        raise ValueError("Test error")
    except Exception as e:
        handler.handle_error(e, "test")