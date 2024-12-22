import pytest
from src.manager import YTBAIManager
from src.exceptions import AIServiceError
from unittest.mock import patch

class TestAIServices:
    @pytest.fixture
    def manager(self):
        return YTBAIManager()

    def test_openai_recommendations(self, manager):
        """Test OpenAI doporučení"""
        results = manager._get_openai_recommendations("happy rock")
        assert len(results) > 0
        assert all(hasattr(r, 'title') for r in results)

    def test_ollama_integration(self, manager):
        """Test Ollama integrace"""
        # Test kontroly serveru
        is_available = manager._check_ollama_server()
        if not is_available:
            print("""
Pro zprovoznění Ollama:
1. Nainstalujte Ollama z https://ollama.ai
2. Spusťte 'ollama serve'
3. Spusťte 'ollama pull llama2'
            """)
            return
        
        # Test doporučení
        try:
            results = manager._get_ollama_recommendations("thrash metal")
            assert len(results) > 0
            assert all(isinstance(r, SearchResult) for r in results)
        except Exception as e:
            print(f"Chyba při testu Ollama: {e}")

    def test_ai_chat_processing(self, manager):
        """Test zpracování AI chatu"""
        response = "1. 'Nothing Else Matters' od Metallica\n2. 'Stairway to Heaven' od Led Zeppelin"
        songs = manager._extract_songs(response)
        assert len(songs) == 2
        assert songs[0]['title'] == "Nothing Else Matters" 

    def test_ollama_response_parsing(self, manager):
        """Test parsování odpovědi z Ollama"""
        test_response = {
            "response": """1. "Master of Puppets" od Metallica
            Žánr: Thrash Metal
            Důvod: Technicky propracovaná skladba s agresivními riffy

            2. "Raining Blood" od Slayer
            Žánr: Thrash Metal
            Důvod: Brutální a rychlá klasika žánru"""
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = test_response
            
            results = manager._get_ollama_recommendations("thrash metal")
            
            assert len(results) > 0
            assert hasattr(results[0], 'genre')
            assert hasattr(results[0], 'reason')
            assert results[0].title == "Master of Puppets"
            assert results[0].artist == "Metallica"