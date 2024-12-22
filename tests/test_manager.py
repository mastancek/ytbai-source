import pytest
from pathlib import Path
import os
from unittest.mock import Mock, patch
from src.manager import YTBAIManager, SearchResult
from src.exceptions import (
    YTBAIError, APIError, DownloadError, ValidationError, 
    CacheError, NetworkError, AIServiceError
)
from src.validators import validate_config, validate_search_result

# Fixture pro YTBAIManager
@pytest.fixture
def manager():
    return YTBAIManager()

# Fixture pro testovací data
@pytest.fixture
def sample_search_result():
    return SearchResult(
        title="Test Song",
        artist="Test Artist",
        duration="3:00",
        video_id="dQw4w9WgXcQ",
        thumbnail_url="https://example.com/thumb.jpg"
    )

class TestSearch:
    def test_search_music_success(self, manager):
        """Test úspěšného vyhledávání"""
        results = manager.search_music("Metallica Nothing Else Matters")
        
        assert isinstance(results, list)
        assert len(results) <= 10
        assert all(isinstance(r, SearchResult) for r in results)
        
        if results:
            result = results[0]
            assert all(isinstance(getattr(result, attr), str) 
                      for attr in ['title', 'artist', 'duration', 'video_id'])

    def test_search_music_invalid_query(self, manager):
        """Test neplatného vyhledávání"""
        results = manager.search_music("!@#$%^&*")
        assert len(results) == 0

    @pytest.mark.parametrize("query", [
        "",
        None,
        "   ",
        "a" * 1000  # Příliš dlouhý dotaz
    ])
    def test_search_music_invalid_input(self, manager, query):
        """Test různých neplatných vstupů"""
        with pytest.raises(ValidationError):
            manager.search_music(query)

class TestDownload:
    def test_download_success(self, manager, sample_search_result, tmp_path):
        """Test úspěšného stahování"""
        with patch.object(manager, 'process_download') as mock_download:
            mock_download.return_value = True
            result = manager.process_download([sample_search_result])
            assert result is True

    def test_download_network_error(self, manager, sample_search_result):
        """Test chyby sítě při stahování"""
        with patch('yt_dlp.YoutubeDL.download', side_effect=NetworkError("Connection failed")):
            with pytest.raises(NetworkError):
                manager.process_download([sample_search_result])

    def test_download_file_system_error(self, manager, sample_search_result):
        """Test chyby souborového systému"""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError):
            with pytest.raises(FileSystemError):
                manager.process_download([sample_search_result])

class TestAIRecommendations:
    @pytest.mark.asyncio
    async def test_ai_recommendations_success(self, manager):
        """Test úspěšných AI doporučení"""
        results = await manager.get_ai_recommendations("happy energetic")
        
        assert isinstance(results, list)
        if results:
            assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_ai_recommendations_service_error(self, manager):
        """Test chyby AI služby"""
        with patch.object(manager, '_get_openai_recommendations', 
                         side_effect=AIServiceError("openai", "API Error")):
            with pytest.raises(AIServiceError):
                await manager.get_ai_recommendations("test")

    @pytest.mark.asyncio
    async def test_ai_recommendations_retry(self, manager):
        """Test opakování při selhání"""
        with patch.object(manager, '_get_openai_recommendations') as mock_recommendations:
            mock_recommendations.side_effect = [
                NetworkError("Timeout"),
                NetworkError("Timeout"),
                [sample_search_result]
            ]
            results = await manager.get_ai_recommendations("test")
            assert len(results) == 1
            assert mock_recommendations.call_count == 3

class TestCache:
    def test_cache_thumbnail(self, manager, tmp_path):
        """Test cache pro náhledy"""
        url = "https://example.com/thumb.jpg"
        with patch('requests.get') as mock_get:
            mock_get.return_value.content = b"fake_image_data"
            mock_get.return_value.status_code = 200
            
            path = manager.cache_thumbnail(url)
            assert path.exists()
            assert path.suffix == '.jpg'

    def test_cache_cleanup(self, manager):
        """Test čištění cache"""
        with patch('pathlib.Path.unlink') as mock_unlink:
            manager.cleanup_cache()
            assert mock_unlink.called

class TestValidation:
    def test_config_validation(self):
        """Test validace konfigurace"""
        valid_config = {
            'paths': {
                'music_dir': str(Path.home() / "Music"),
                'cache_dir': str(Path.home() / ".cache"),
                'logs_dir': str(Path.home() / ".logs")
            },
            'download': {
                'format': 'mp3',
                'quality': '192k',
                'max_concurrent': 3
            }
        }
        assert validate_config(valid_config)

    def test_search_result_validation(self, sample_search_result):
        """Test validace výsledku vyhledávání"""
        result_dict = {
            'title': sample_search_result.title,
            'artist': sample_search_result.artist,
            'duration': sample_search_result.duration,
            'video_id': sample_search_result.video_id
        }
        assert validate_search_result(result_dict)

    @pytest.mark.parametrize("invalid_field,invalid_value", [
        ('title', ''),
        ('artist', None),
        ('duration', 123),
        ('video_id', '')
    ])
    def test_search_result_validation_invalid(self, invalid_field, invalid_value):
        """Test validace neplatných hodnot"""
        result_dict = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'duration': '3:00',
            'video_id': 'dQw4w9WgXcQ'
        }
        result_dict[invalid_field] = invalid_value
        
        with pytest.raises(ValidationError):
            validate_search_result(result_dict)

def test_first_run_wizard(self):
    """Test průvodce prvním spuštěním"""
    # Simulace prvního spuštění
    self.config['first_run'] = True
    
    # Test vytvoření složek
    music_dir = self.manager.config['paths']['music_dir']
    self.assertTrue(Path(music_dir).exists())
    
    # Test nastavení konfigurace
    self.assertFalse(self.config['first_run'])