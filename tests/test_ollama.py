import pytest
import requests
from unittest.mock import patch, Mock
from src.manager import YTBAIManager
from src.exceptions import ConfigError

class TestOllamaIntegration:
    @pytest.fixture
    def manager(self):
        return YTBAIManager()

    def test_ollama_server_check(self, manager):
        """Test kontroly dostupnosti Ollama serveru"""
        # Test když server běží
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            assert manager._check_ollama_server() is True

        # Test když server neběží
        with patch('requests.get', side_effect=requests.ConnectionError):
            assert manager._check_ollama_server() is False

    def test_ollama_model_list(self, manager):
        """Test získání seznamu modelů"""
        mock_response = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"},
                {"name": "codellama"}
            ]
        }
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            models = manager._get_local_ollama_models()
            assert "llama2" in models
            assert len(models) == 3

    def test_ollama_recommendations(self, manager):
        """Test získání doporučení od Ollama"""
        mock_response = {
            "response": """Tady jsou doporučení:
            1. "Nothing Else Matters" od Metallica - Klasická metalová balada
            2. "Stairway to Heaven" od Led Zeppelin - Legendární skladba
            3. "Bohemian Rhapsody" od Queen - Epická rocková opera"""
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            results = manager._get_ollama_recommendations("rock ballads")
            assert len(results) > 0
            assert any("Metallica" in r.artist for r in results)

    def test_ollama_error_handling(self, manager):
        """Test zpracování chyb Ollama"""
        # Test když server není dostupný
        with patch('requests.post', side_effect=requests.ConnectionError):
            with pytest.raises(ConfigError) as exc_info:
                manager._get_ollama_recommendations("test")
            assert "Ollama server není dostupný" in str(exc_info.value)

        # Test neplatné odpovědi
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.side_effect = ValueError
            with pytest.raises(ConfigError) as exc_info:
                manager._get_ollama_recommendations("test")
            assert "Chyba při komunikaci s Ollama" in str(exc_info.value)

    def test_ollama_prompt_format(self, manager):
        """Test formátování promptu pro Ollama"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"response": "test"}
            
            manager._get_ollama_recommendations("rock")
            
            # Kontrola struktury promptu
            called_json = mock_post.call_args.kwargs['json']
            assert 'model' in called_json
            assert 'prompt' in called_json
            assert 'hudební expert' in called_json['prompt'].lower()
            assert 'rock' in called_json['prompt'].lower()

    def test_ollama_response_parsing(self, manager):
        """Test parsování odpovědi od Ollama"""
        test_response = {
            "response": """
            1. "Master of Puppets" od Metallica - Thrash metal klasika
            2. "Holy Wars" od Megadeth - Technický thrash
            3. "Painkiller" od Judas Priest - Speed metal hymna
            """
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = test_response
            
            results = manager._get_ollama_recommendations("metal")
            
            assert len(results) == 3
            assert results[0].title == "Master of Puppets"
            assert results[0].artist == "Metallica"
            assert results[1].artist == "Megadeth"

    @pytest.mark.asyncio
    async def test_ollama_async_chat(self, manager):
        """Test asynchronní komunikace s Ollama"""
        mock_response = {"response": "Test odpověď"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_response
            response = await manager._async_ollama_chat("Test prompt")
            assert response is not None
            assert isinstance(response, str)

    def test_ollama_model_management(self, manager):
        """Test správy modelů Ollama"""
        # Test stažení modelu
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            assert manager._download_ollama_model("llama2") is True

        # Test odstranění modelu
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            assert manager._remove_ollama_model("llama2") is True 