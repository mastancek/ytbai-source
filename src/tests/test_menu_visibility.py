import pytest
from src.ui.core import UICore
from rich.console import Console

def test_subsequent_text_visibility(capsys, monkeypatch):
    """Test viditelnosti následujících textů"""
    console = Console()
    ui_core = UICore(console, {'theme': 'dracula'})
    
    # Použijeme monkeypatch pro input
    monkeypatch.setattr('builtins.input', lambda: "1")
    
    # Test sekvence akcí
    ui_core.show_main_menu()
    console.print("Test následujícího textu")
    
    captured = capsys.readouterr()
    
    # Kontroly
    assert "Vyberte možnost" in captured.out
    assert "Zvolena možnost: 1" in captured.out
    assert "Test následujícího textu" in captured.out 