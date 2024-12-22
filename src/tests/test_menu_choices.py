def test_menu_choices(capsys):
    """Test zpracování voleb v menu"""
    console = Console()
    config = {'theme': 'dracula'}
    ui = UI(YTBAIManager(), console)
    
    # Test volby 1 (YouTube vyhledávání)
    ui._handle_youtube_search = lambda: None  # Mock
    ui._process_menu_choice("1")
    captured = capsys.readouterr()
    assert "YouTube vyhledávání" in captured.out 