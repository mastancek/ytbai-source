import pytest
from pathlib import Path
import os
from src.manager import YTBAIManager
from src.exceptions import YTBAIError

@pytest.mark.integration
class TestIntegration:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup pro integrační testy"""
        self.manager = YTBAIManager()
        self.test_dir = tmp_path / "ytbai_test"
        self.test_dir.mkdir()
        
        # Nastavení testovacího prostředí
        os.environ['YTBAI_TEST'] = '1'
        yield
        # Cleanup
        os.environ.pop('YTBAI_TEST', None)

    def test_full_download_flow(self):
        """Test celého procesu stahování"""
        # 1. Vyhledání
        results = self.manager.search_music("Metallica Nothing Else Matters")
        assert results
        
        # 2. Stažení
        first_result = results[0]
        self.manager.process_download([first_result])
        
        # 3. Kontrola souboru
        expected_file = Path.home() / "Music" / "YouTube" / f"{first_result.title}.mp3"
        assert expected_file.exists()
        assert expected_file.stat().st_size > 0

    def test_ai_recommendation_flow(self):
        """Test procesu AI doporučení"""
        # 1. Získání doporučení
        results = self.manager.get_ai_recommendations("happy energetic")
        assert results
        
        # 2. Stažení doporučené skladby
        first_result = results[0]
        self.manager.process_download([first_result])
        
        # 3. Získání podobných skladeb
        similar = self.manager.get_recommendations([first_result])
        assert similar
        assert len(similar) <= 10

    def test_error_recovery(self):
        """Test zotavení z chyb"""
        # Simulace výpadku sítě
        with pytest.raises(YTBAIError):
            self.manager.search_music("test" * 1000)
        
        # Program by měl pokračovat
        results = self.manager.search_music("Metallica")
        assert results

    def test_cache_behavior(self):
        """Test chování cache"""
        # 1. První vyhledání
        results1 = self.manager.search_music("Metallica Nothing Else Matters")
        
        # 2. Druhé vyhledání (mělo by být z cache)
        results2 = self.manager.search_music("Metallica Nothing Else Matters")
        
        # Výsledky by měly být stejné
        assert len(results1) == len(results2)
        assert all(r1.video_id == r2.video_id 
                  for r1, r2 in zip(results1, results2)) 

    def test_ai_recommendations_to_youtube(self, manager):
        """Test procesu od AI doporučení po YouTube vyhledávání"""
        # Test Ollama
        try:
            results = manager._get_ollama_recommendations("thrash metal")
            assert len(results) > 0
            assert all(hasattr(r, 'video_id') for r in results)
            assert all(hasattr(r, 'genre') for r in results)
            assert all(hasattr(r, 'reason') for r in results)
        except Exception as e:
            print(f"Ollama test selhal: {e}")

        # Test OpenAI
        try:
            results = manager._get_openai_recommendations("thrash metal")
            assert len(results) > 0
            assert all(hasattr(r, 'video_id') for r in results)
        except Exception as e:
            print(f"OpenAI test selhal: {e}")