import pytest
from pathlib import Path
from rich.console import Console
from src.manager.ytbai_manager import YTBAIManager, SearchResult
from src.utils.error_handler import ErrorHandler

@pytest.fixture
def manager():
    return YTBAIManager()

def test_search_basic(manager):
    """Test základního vyhledávání"""
    results = manager.search_music("mládek žába")
    
    assert len(results) > 0, "Vyhledávání by mělo vrátit výsledky"
    assert isinstance(results[0], SearchResult), "Výsledek by měl být instance SearchResult"
    
    # Kontrola prvního výsledku
    first = results[0]
    assert first.video_id, "Video ID by nemělo být prázdné"
    assert first.title, "Název by neměl být prázdný"
    assert first.artist, "Interpret by neměl být prázdný"
    assert ":" in first.duration, "Délka by měla být ve formátu MM:SS"

def test_search_empty(manager):
    """Test prázdného vyhledávání"""
    results = manager.search_music("")
    assert len(results) == 0, "Prázdný dotaz by měl vrátit prázdný seznam"

def test_search_normalize_filename(manager):
    """Test normalizace názvu souboru"""
    filename = "Žába - Puk (Live) @ Festival"
    normalized = manager._normalize_filename(filename)
    
    assert " " not in normalized, "Název by neměl obsahovat mezery"
    assert "Ž" not in normalized, "Název by neměl obsahovat diakritiku"
    assert "@" not in normalized, "Název by neměl obsahovat speciální znaky"
    assert normalized == "Zaba_-_Puk_Live_Festival"

def test_download_song(manager, tmp_path):
    """Test stahování skladby"""
    # Nastavení dočasné složky pro stahování
    manager.config['paths']['music_dir'] = str(tmp_path)
    
    # Vyhledání a stažení první skladby
    results = manager.search_music("mládek žába")
    assert results, "Měly by být nalezeny výsledky"
    
    success = manager.download_song(results[0])
    assert success, "Stahování by mělo být úspěšné"
    
    # Kontrola staženého souboru
    files = list(tmp_path.glob("*.mp3"))
    assert files, "Měl by existovat stažený soubor"
    assert files[0].stat().st_size > 0, "Soubor by neměl být prázdný"

def test_download_status_tracking(manager, tmp_path):
    """Test sledování stavu stahování"""
    manager.config['paths']['music_dir'] = str(tmp_path)
    
    results = manager.search_music("mládek žába")
    first_result = results[0]
    
    # První stažení
    assert not manager._is_song_downloaded(first_result.video_id), "Skladba by neměla být označena jako stažená"
    success = manager.download_song(first_result)
    assert success, "První stažení by mělo být úspěšné"
    assert manager._is_song_downloaded(first_result.video_id), "Skladba by měla být označena jako stažená"
    
    # Pokus o opětovné stažení
    success = manager.download_song(first_result)
    assert success, "Druhé stažení by mělo být 'úspěšné' (skladba už existuje)"

def test_search_result_metadata(manager):
    """Test metadat výsledků vyhledávání"""
    results = manager.search_music("mládek žába")
    first = results[0]
    
    assert first.thumbnail_url, "Měla by být dostupná URL náhledu"
    assert first.views is not None, "Měl by být dostupný počet zhlédnutí"
    assert first.upload_date, "Mělo by být dostupné datum nahrání"
    assert first.thumbnail_path, "Měla by být dostupná cesta k náhledu"

if __name__ == "__main__":
    # Ruční spuštění testů
    manager = YTBAIManager()
    
    print("Test vyhledávání...")
    test_search_basic(manager)
    
    print("Test stahování...")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_download_song(manager, Path(tmp))
    
    print("Všechny testy dokončeny!") 