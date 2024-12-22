import pytest
from src.manager.ytbai_manager import YTBAIManager

def test_search():
    manager = YTBAIManager()
    
    # Test 1: Základní vyhledávání
    results = manager.search_music("mládek u lesícka zaba")
    assert len(results) > 0, "Vyhledávání by mělo vrátit výsledky"
    
    # Test 2: Kontrola formátu výsledků
    first_result = results[0]
    assert first_result.video_id, "Video ID by nemělo být prázdné"
    assert first_result.title, "Název by neměl být prázdný"
    assert first_result.artist, "Interpret by neměl být prázdný"
    assert ":" in first_result.duration, "Délka by měla být ve formátu MM:SS"
    
    # Test 3: Prázdný dotaz
    empty_results = manager.search_music("")
    assert len(empty_results) == 0, "Prázdný dotaz by měl vrátit prázdný seznam" 