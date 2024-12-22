from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
from spotdl import Spotdl
from ..manager.ytbai_manager import SearchResult
from dotenv import load_dotenv
import os

logger = logging.getLogger('ytbai.spotify')
fh = logging.FileHandler('ytbai.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

class SpotifyManager:
    def __init__(self, config: dict):
        # Načteme proměnné z .env souboru
        load_dotenv()
        
        # Prioritně použijeme hodnoty z .env, pak z config
        self.config = config
        
        # Zajistíme, že klíče jsou v ASCII
        client_id = (os.getenv('SPOTIFY_CLIENT_ID') or 
                    config.get('spotify', {}).get('client_id', '')).encode('ascii', 'ignore').decode()
        client_secret = (os.getenv('SPOTIFY_CLIENT_SECRET') or 
                        config.get('spotify', {}).get('client_secret', '')).encode('ascii', 'ignore').decode()
        
        logger.debug(f"Client ID length: {len(client_id)}")
        logger.debug(f"Client Secret length: {len(client_secret)}")
        
        if not client_id or not client_secret:
            raise ValueError("Spotify API klíče nejsou nastaveny nebo jsou neplatné")
        
        # Nastavení výstupního adresáře a kvality
        self.output_dir = Path(config['paths']['music_dir'])
        self.quality = config.get('spotify', {}).get('quality', '320k')
        
        # Cesta k ffmpeg
        ffmpeg_path = Path(__file__).parent.parent.parent / 'bin'
        if not (ffmpeg_path / 'ffmpeg.exe').exists():
            logger.error(f"ffmpeg není nalezen v: {ffmpeg_path}")
            raise FileNotFoundError(f"ffmpeg není nalezen v: {ffmpeg_path}")
        
        # Nastavení proměnné prostředí pro ffmpeg
        os.environ["PATH"] = f"{str(ffmpeg_path)};{os.environ['PATH']}"
        
        try:
            # Inicializace spotdl s novým rozhraním
            self.spotdl = Spotdl(
                client_id=client_id,
                client_secret=client_secret
            )
            logger.info("SpotifyManager úspěšně inicializován")
        except Exception as e:
            logger.error(f"Chyba při inicializaci Spotify: {e}", exc_info=True)
            raise
        
        # Nastavení výchozích parametrů pro stahování
        self.download_settings = {
            'output': str(self.output_dir),
            'format': 'mp3',
            'bitrate': self.quality,
            'save_file': True
        }

    def search_music(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Vyhledá hudbu na Spotify"""
        try:
            logger.info(f"Začínám vyhledávání na Spotify: {query}")
            
            # Vyhledání na Spotify
            results = self.spotdl.search([query])
            logger.debug(f"Spotify vrátil {len(results)} výsledků")
            
            # Konverze na naše SearchResult objekty
            converted_results = []
            for i, result in enumerate(results[:limit], 1):
                try:
                    logger.debug(f"Zpracovávám výsledek {i}: {result.name}")
                    converted = SearchResult(
                        video_id=result.url,
                        title=result.name,
                        artist=result.artist,
                        duration=self._format_duration(result.duration),
                        genre=result.genres[0] if result.genres else None,
                        tags=result.genres,
                        thumbnail_url=result.cover_url,
                        audio_quality="320k",
                        audio_format="mp3"
                    )
                    converted_results.append(converted)
                    logger.debug(f"Výsledek {i} úspěšně převeden")
                except Exception as e:
                    logger.warning(f"Chyba při konverzi skladby {i}: {e}", exc_info=True)
                    continue
            
            logger.info(f"Úspěšně převedeno {len(converted_results)} výsledků")
            return converted_results
            
        except Exception as e:
            logger.error(f"Chyba při vyhledávání na Spotify: {e}", exc_info=True)
            return []

    def download_song(self, result: SearchResult, output_dir: Path) -> Optional[Path]:
        """Stáhne skladbu ze Spotify"""
        try:
            # Aktualizace výstupního adresáře pro tento download
            download_opts = self.download_settings.copy()
            download_opts['output'] = str(output_dir)
            
            # Stažení pomocí spotdl s parametry
            downloaded = self.spotdl.download(
                result.video_id,
                **download_opts
            )
            if downloaded:
                return Path(downloaded[0])
            return None
            
        except Exception as e:
            logger.error(f"Chyba při stahování ze Spotify: {e}")
            return None

    def _format_duration(self, ms: int) -> str:
        """Formátuje délku z milisekund na MM:SS"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}" 

    def get_playlist_tracks(self, playlist_url: str) -> List[SearchResult]:
        """Získá skladby z playlistu"""
        try:
            playlist = self.spotdl.get_playlist_tracks(playlist_url)
            return self._convert_to_search_results(playlist)
        except Exception as e:
            logger.error(f"Chyba při získávání playlistu: {e}")
            return []

    def get_artist_top_tracks(self, artist_url: str) -> List[SearchResult]:
        """Získá nejpopulárnější skladby interpreta"""
        try:
            top_tracks = self.spotdl.get_artist_top_tracks(artist_url)
            return self._convert_to_search_results(top_tracks)
        except Exception as e:
            logger.error(f"Chyba při získávání top skladeb: {e}")
            return []

    def get_audio_features(self, track_id: str) -> Dict[str, Any]:
        """Získá hudební charakteristiky skladby"""
        try:
            features = self.spotdl.get_audio_features(track_id)
            return {
                'danceability': features.get('danceability'),
                'energy': features.get('energy'),
                'key': features.get('key'),
                'loudness': features.get('loudness'),
                'mode': features.get('mode'),
                'tempo': features.get('tempo'),
                'time_signature': features.get('time_signature')
            }
        except Exception as e:
            logger.error(f"Chyba při získávání audio features: {e}")
            return {}