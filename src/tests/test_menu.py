import pytest
from src.ui.core import UICore
from rich.console import Console
from io import StringIO
import sys

class TestMenu:
    @pytest.fixture
    def ui_core(self):
        console = Console()
        config = {'theme': 'dracula'}
        return UICore(console, config)

    def test_menu_content(self, ui_core, capsys):
        """Test obsahu menu"""
        def mock_input():
            return "1"
        ui_core._get_input = mock_input
        
        # Zobrazíme menu
        ui_core.show_main_menu()
        captured = capsys.readouterr()
        
        # Kontrola přítomnosti všech položek menu
        menu_items = [
            "1. YouTube vyhledávání",
            "2. AI doporučení hudby",
            "3. Upřesnit vyhledávání",
            "4. Chat s hudebním AI",
            "5. Správa AI služeb",
            "6. Správa nastavení",
            "7. Přehrávač hudby",
            "8. Webshare stahování",
            "9. Spotify vyhledávání",
            "K. Konec"
        ]
        
        for item in menu_items:
            assert item in captured.out, f"Položka '{item}' chybí v menu"

    def test_menu_input_handling(self, ui_core, monkeypatch):
        """Test zpracování různých vstupů"""
        test_cases = [
            ("1", "1"),
            ("k", "K"),
            (" 9 ", "9"),
            ("K", "K"),
            ("", "")
        ]
        
        for test_input, expected in test_cases:
            # Použijeme monkeypatch místo mock_input
            monkeypatch.setattr('builtins.input', lambda: test_input)
            assert ui_core.show_main_menu() == expected

    def test_menu_sections(self, ui_core, capsys):
        """Test oddělení sekcí menu"""
        def mock_input():
            return "1"
        ui_core._get_input = mock_input
        
        ui_core.show_main_menu()
        captured = capsys.readouterr()
        
        # Kontrola oddělení sekcí
        sections = [
            "Vyhledávání a stahování",
            "AI a nastavení",
            "Přehrávání a stahování"
        ]
        
        menu_text = captured.out
        for section in sections:
            assert any(section in line for line in menu_text.split('\n')), f"Sekce '{section}' chybí v menu"