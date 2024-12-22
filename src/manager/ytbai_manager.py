from typing import List, Dict, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TransferSpeedColumn
import yt_dlp
from ..utils.error_handler import ErrorHandler
import re
import unicodedata
import subprocess
import requests
import json
from mutagen.id3 import ID3, TIT2, TPE1, APIC
import shutil
from PIL import Image
from io import BytesIO
import logging

# Nastavení loggeru
logger = logging.getLogger('ytbai.manager')
logger.setLevel(logging.INFO)  # Změna z DEBUG na INFO

class SearchResult:
    def __init__(self, video_id: str, title: str, artist: str, duration: str, 
                 genre: str = None, tags: List[str] = None, 
                 thumbnail_url: str = None, size: Optional[int] = None,
                 audio_quality: Optional[str] = None,
                 audio_format: Optional[str] = None):
        self.video_id = video_id
        self.title = title
        self.artist = artist
        self.duration = duration
        self.genre = genre
        self.tags = tags or []
        self.thumbnail_url = thumbnail_url
        self.size = size
        self.audio_quality = audio_quality
        self.audio_format = audio_format
        self._thumbnail_path = None

    @property
    def thumbnail_path(self) -> Optional[Path]:
        """Cesta k náhledu videa"""
        return self._thumbnail_path

    @thumbnail_path.setter
    def thumbnail_path(self, path: Path):
        self._thumbnail_path = path

class SearchPreferences:
    def __init__(self):
        self.exclude = {
            'covers': True,
            'live': False,
            'remixes': True,
            'revivals': True,
            'karaoke': True
        }
        self.prefer = {
            'official': True,
            'albums': False,
            'original': True,
            'studio': True
        }
        self.filters = {
            'min_duration': 0,
            'max_duration': 0,
            'min_quality': '192k',
            'language': 'any'
        }

    def apply_to_results(self, results: List[SearchResult]) -> List[SearchResult]:
        filtered = []
        for result in results:
            if self._should_include(result):
                filtered.append(result)
        return sorted(filtered, key=lambda x: self._calculate_preference_score(x), reverse=True)

class YTBAIManager:
    def __init__(self):
        self._config = None
        self._error_handler = None
        self._spotify = None
        self._youtube = None
        self._ai_models = None
        self._progress = None
        
    @property
    def config(self):
        if self._config is None:
            self._config = load_config()
        return self._config
        
    @property
    def error_handler(self):
        if self._error_handler is None:
            self._error_handler = ErrorHandler(self.console)
        return self._error_handler
    
    @property
    def progress(self):
        if self._progress is None:
            self._progress = self._setup_progress()
        return self._progress

    @property
    def console(self):
        # Sdílíme jednu instanci konzole z UI
        return self._console
    
    def initialize(self, console: Console):
        """Inicializace s existující konzolí"""
        self._console = console

    @property
    def spotify(self):
        """Lazy loading pro Spotify"""
        if self._spotify is None:
            self._spotify = SpotifyManager(self.config)
        return self._spotify

    @property
    def youtube(self):
        """Lazy loading pro YouTube"""
        if self._youtube is None:
            self._youtube = YouTubeManager(self.config)
        return self._youtube

    @property
    def ai_models(self):
        """Lazy loading pro AI modely"""
        if self._ai_models is None:
            self._ai_models = AIModelManager(self.config)
        return self._ai_models

    def _setup_progress(self):
        """Inicializace progress baru"""
        if self.progress and self.progress.live:
            self.progress.stop()
            
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            TransferSpeedColumn(),
            TextColumn("[cyan]{task.fields[status]}[/cyan]"),
            console=self.console,
            expand=True  # Přidáno pro lepší zobrazení
        )

    def _check_free_space(self, required_bytes: int) -> bool:
        """Kontrola volného místa na disku"""
        music_dir = Path(self.config['paths']['music_dir'])
        free_space = shutil.disk_usage(music_dir).free
        return free_space > required_bytes * 1.5  # 50% rezerva

    def _download_and_resize_cover(self, url: str, size: tuple = (300, 300)) -> Optional[bytes]:
        """Stáhne a upraví velikost cover art"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Otevření a resize obrázku
            img = Image.open(BytesIO(response.content))
            img = img.convert('RGB')  # Konverze na RGB
            img.thumbnail(size)  # Zachová poměr stran
            
            # Konverze zpět na bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=90)
            return output.getvalue()
            
        except Exception as e:
            self.error_handler.warning(f"Chyba při stahování cover art: {e}")
            return None

    def _add_cover_to_mp3(self, file_path: Path, cover_data: bytes) -> bool:
        """Přidá cover art do MP3 souboru"""
        try:
            audio = ID3(str(file_path))
            
            # Přidání cover art
            audio.add(APIC(
                encoding=3,  # UTF-8
                mime='image/jpeg',
                type=3,  # Cover (front)
                desc='Cover',
                data=cover_data
            ))
            
            audio.save()
            return True
            
        except Exception as e:
            self.error_handler.warning(f"Chyba při ukládání cover art: {e}")
            return False

    def _organize_downloaded_file(self, file_path: Path, result: SearchResult) -> Path:
        """Organizuje stažené soubory do složek podle interpreta"""
        try:
            artist_dir = Path(self.config['paths']['music_dir']) / self._normalize_filename(result.artist)
            artist_dir.mkdir(exist_ok=True)
            
            # Přidání metadat
            audio = ID3(str(file_path))
            audio['TIT2'] = TIT2(text=[result.title])
            audio['TPE1'] = TPE1(text=[result.artist])
            
            # Přidání cover art
            if result.thumbnail_url:
                cover_size = self.config.get('cover_art', {}).get('size', (300, 300))
                cover_data = self._download_and_resize_cover(result.thumbnail_url, cover_size)
                if cover_data:
                    self._add_cover_to_mp3(file_path, cover_data)
            
            audio.save()
            
            new_path = artist_dir / file_path.name
            return file_path.rename(new_path)
            
        except Exception as e:
            self.error_handler.warning(f"Chyba při organizaci souboru: {e}")
            return file_path

    def _normalize_filename(self, filename: str) -> str:
        """Normalizuje název souboru - odstranění diakritiky a neplatné znaky"""
        # Převod na základní znaky (odstranění diakritiky)
        filename = unicodedata.normalize('NFKD', filename)
        filename = ''.join(c for c in filename if not unicodedata.combining(c))
        
        # Odstranění neplatných znaků pro název souboru
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Nahrazení mezer podtržítkem a odstranění více podtržítek za sebou
        filename = re.sub(r'\s+', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        
        # Odstranění podtržek na začátku a konci
        filename = filename.strip('_')
        
        return filename

    def _normalize_audio(self, file_path: Path) -> bool:
        """Normalizuje hlasitost MP3 souboru pomocí mp3gain"""
        try:
            mp3gain_path = Path(self.config['paths']['ffmpeg_dir']) / 'mp3gain.exe'
            if not mp3gain_path.exists():
                self.error_handler.warning("mp3gain.exe nenalezen v bin/ složce")
                return False

            self.error_handler.info(f"Normalizuji hlasitost: {file_path.name}")
            
            # Spuštění mp3gain s parametry:
            # -r = apply Track gain automatically (89.0 dB)
            # -k = automatically lower Track/Album gain to not clip audio
            # -c = ignore clipping warning when applying gain
            process = subprocess.run(
                [str(mp3gain_path), "-r", "-k", "-c", str(file_path)],
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                self.error_handler.info(f"Hlasitost normalizována: {file_path.name}")
                return True
            else:
                self.error_handler.warning(f"Chyba při normalizaci: {process.stderr}")
                return False
            
        except Exception as e:
            self.error_handler.error(f"Chyba při normalizaci zvuku: {e}")
            return False

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """Hook pro zobrazení průběhu stahování"""
        try:
            if d['status'] == 'downloading' and self.progress and self.current_task_id:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                
                if total > 0:
                    percentage = (downloaded / total) * 100
                    self.progress.update(
                        self.current_task_id,
                        completed=percentage,
                        description=f"Stahuji: {d.get('filename', '')}",
                        status=f"Rychlost: {speed/1024/1024:.1f} MB/s" if speed else ""
                    )
        except Exception as e:
            self.error_handler.warning(f"Chyba v progress_hook: {e}")

    def download_song(self, result: SearchResult, is_last: bool = False) -> bool:
        """Stáhne skladbu z YouTube"""
        try:
            # Kontrola volného místa
            required_space = result.size or 1024 * 1024 * 50  # 50MB minimum
            if not self._check_free_space(required_space):
                self.error_handler.warning("Nedostatek místa na disku")
                return False
                
            # Kontrola duplicit
            if self._is_song_downloaded(result.video_id):
                self.error_handler.info(f"Skladba již existuje: {result.title}")
                return True
                
            music_dir = Path(self.config['paths']['music_dir'])
            normalized_title = self._normalize_filename(f"{result.artist} - {result.title}")
            output_path = music_dir / f"{normalized_title}.mp3"
            
            # Inicializace progress baru
            if not hasattr(self, 'progress') or self.progress is None:
                self._setup_progress()
            
            # Spuštění progress baru
            if not self.progress.live:
                self.progress.start()
            
            # Vytvoření nebo aktualizace tasku
            if self.current_task_id is None:
                self.current_task_id = self.progress.add_task(
                    description=f"Stahuji: {result.title}",
                    total=100,  # Nastavíme celkový progres na 100%
                    completed=0,
                    status="Příprava..."
                )
            else:
                self.progress.update(
                    self.current_task_id,
                    description=f"Stahuji: {result.title}",
                    completed=0,
                    status="Příprava..."
                )
            
            # Důležité - nastavení progress_task na self.progress
            self.progress_task = self.progress
            
            # Stahování
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(output_path),
                'quiet': True,
                'no_warnings': True,
                'logger': self.error_handler,
                'ffmpeg_location': str(Path(self.config['paths']['ffmpeg_dir'])),
                'progress_hooks': [self._progress_hook]
            }
            
            url = f"https://www.youtube.com/watch?v={result.video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Dokončení
            if output_path.exists():
                output_path = self._organize_downloaded_file(output_path, result)
                self._mark_as_downloaded(result.video_id)
                
            if is_last:
                self.progress.stop()
                
            return True
            
        except Exception as e:
            self.error_handler.error(f"Chyba při stahování {result.title}: {e}")
            if hasattr(self, 'progress') and self.progress and self.progress.live:
                self.progress.stop()
            return False

    def _get_thumbnail_cache(self, video_id: str) -> Optional[Path]:
        """Získá cestu k náhledu v cache"""
        cache_dir = Path(self.config['paths']['cache_dir']) / 'thumbnails'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{video_id}.jpg"

    def _download_thumbnail(self, video_id: str, url: str) -> Optional[Path]:
        """Stáhne náhled videa"""
        try:
            cache_path = self._get_thumbnail_cache(video_id)
            if cache_path.exists():
                return cache_path
            
            response = requests.get(url)
            response.raise_for_status()
            
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            return cache_path
        except Exception as e:
            self.error_handler.error(f"Chyba při stahování náhledu: {e}")
            return None

    def _is_song_downloaded(self, video_id: str) -> bool:
        """Zkontroluje, zda je skladba již stažena"""
        try:
            music_dir = Path(self.config['paths']['music_dir'])
            downloaded_file = music_dir / '.downloaded.json'
            
            if not downloaded_file.exists():
                return False
            
            with open(downloaded_file, 'r', encoding='utf-8') as f:
                downloaded = json.load(f)
                return video_id in downloaded
            
        except Exception:
            return False

    def _mark_as_downloaded(self, video_id: str) -> None:
        """Označí skladbu jako staženou"""
        try:
            music_dir = Path(self.config['paths']['music_dir'])
            downloaded_file = music_dir / '.downloaded.json'
            
            downloaded = []
            if downloaded_file.exists():
                with open(downloaded_file, 'r', encoding='utf-8') as f:
                    downloaded = json.load(f)
                
            if video_id not in downloaded:
                downloaded.append(video_id)
            
            with open(downloaded_file, 'w', encoding='utf-8') as f:
                json.dump(downloaded, f)
            
        except Exception as e:
            self.error_handler.error(f"Chyba při ukládání seznamu stažených: {e}")

    def _calculate_relevance(self, entry: Dict[str, Any], query: str) -> float:
        """Vypočítá skóre relevance výsledku"""
        score = 0.0
        
        # Shoda v názvu
        title = entry.get('title', '').lower()
        query = query.lower()
        if query in title:
            score += 1.0
            
        # Délka videa (preferujeme skladby 2-8 minut)
        duration = entry.get('duration', 0)
        if 120 <= duration <= 480:
            score += 0.5
            
        # Počet zhlédnutí
        views = entry.get('view_count', 0)
        if views > 10000:
            score += 0.3
            
        # Oficiální kanál
        if entry.get('channel', '').endswith('- Topic'):
            score += 0.8
            
        return score

    def _extract_genre(self, entry: Dict[str, Any]) -> Optional[str]:
        """Extrahuje žánr z tagů a popisu"""
        tags = entry.get('tags', [])
        description = entry.get('description', '') or ''  # Zajistíme, že description nebude None
        
        # Seznam běžných hudebních žánrů
        genres = {
            'rock', 'pop', 'jazz', 'blues', 'folk', 'country', 
            'metal', 'classical', 'electronic', 'hip hop', 'rap',
            'alternative', 'indie', 'punk', 'reggae', 'soul', 'funk',
            'chanson', 'folk-rock', 'acoustic', 'singer-songwriter'  # Přidány další žánry
        }
        
        # Nejdřív zkusíme najít žánr v tazích
        if tags:
            for tag in tags:
                if not tag:  # Přeskočíme None nebo prázdné tagy
                    continue
                tag_lower = tag.lower()
                if tag_lower in genres:
                    return tag
                # Kontrola složených žánrů
                for genre in genres:
                    if genre in tag_lower:
                        return genre
        
        # Pak v popisu
        description_lower = description.lower()
        for genre in genres:
            if genre in description_lower:
                return genre
        
        # Pokud nenajdeme žánr, zkusíme odhadnout z kontextu
        context_hints = {
            'koncert': 'live',
            'live': 'live',
            'acoustic': 'acoustic',
            'unplugged': 'acoustic',
            'písničkář': 'folk',
            'folk': 'folk'
        }
        
        for hint, genre in context_hints.items():
            if hint in description_lower or any(hint in (tag or '').lower() for tag in tags):
                return genre
            
        return None

    def search_music(self, query: str, limit: int = 10, use_related: bool = False, 
                    use_recommendations: bool = False, use_playlists: bool = False) -> List[SearchResult]:
        """Vyhledá hudbu na YouTube s rozšířenými možnostmi"""
        if not query:
            self.error_handler.warning("Prázdný vyhledávací dotaz")
            return []
        
        try:
            # Konfigurace yt-dlp podle parametrů
            ydl_opts = self.ydl_opts.copy()
            
            # Nastavení limitu výsledků
            ydl_opts['playlistend'] = limit
            
            # Nastavení typu vyhledávání
            if use_playlists:
                search_query = f"ytsearchplaylist{limit}:{query}"
            else:
                search_query = f"ytsearch{limit}:{query}"
                
            # Přidání parametrů pro související videa
            if use_related:
                ydl_opts['extract_flat'] = 'in_playlist'
                ydl_opts['playlist_items'] = '1'
                ydl_opts['extract_flat_playlist'] = True
                
            # Přidání parametrů pro doporučení
            if use_recommendations:
                ydl_opts['extract_flat'] = 'in_playlist'
                ydl_opts['playlist_items'] = '1-5'  # První video a jeho doporučení
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.error_handler.info(f"Vyhledávám: {query}")
                
                # Vyhledání videí
                search_results = ydl.extract_info(search_query, download=False)
                
                if not search_results or 'entries' not in search_results:
                    self.error_handler.warning("Žádné výsledky nenalezeny")
                    return []
                    
                results = []
                entries = search_results['entries']
                
                # Pokud hledáme související videa, získáme je
                if use_related and entries:
                    first_video = entries[0]
                    related_results = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={first_video['id']}",
                        download=False
                    )
                    if related_results and 'related_videos' in related_results:
                        entries.extend(related_results['related_videos'][:limit-1])
                
                # Zpracování výsledků
                for entry in entries:
                    if not entry:
                        continue
                        
                    # Extrakce informací
                    result = self._extract_video_info(entry)
                    if result:
                        results.append(result)
                        
                    if len(results) >= limit:
                        break
                
                self.error_handler.info(f"Nalezeno {len(results)} výsledků")
                return results
                
        except Exception as e:
            self.error_handler.error(f"Chyba při vyhledávání: {e}")
            return []

    def _extract_video_info(self, entry: Dict[str, Any]) -> Optional[SearchResult]:
        """Extrahuje informace o videu"""
        try:
            video_id = entry.get('id', '')
            title = entry.get('title', 'Neznámý název')
            
            # Extrakce žánru a tagů
            genre = entry.get('genre') or self._extract_genre(entry)
            tags = [tag.strip() for tag in entry.get('tags', []) if tag and isinstance(tag, str)]
            
            # Extrakce interpreta
            artist = entry.get('artist', '')
            if not artist and ' - ' in title:
                artist = title.split(' - ')[0].strip()
                title = title.split(' - ')[1].strip()
            elif not artist:
                artist = entry.get('channel', 'Neznámý interpret')
            
            # Formátování délky
            try:
                duration = int(entry.get('duration', 0))
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            except (TypeError, ValueError):
                duration_str = "--:--"
            
            # Extrakce informací o audio kvalitě
            formats = entry.get('formats', [])
            audio_format = None
            audio_quality = None
            
            # Najdeme nejlepší audio formát
            for fmt in formats:
                if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':  # pouze audio
                    abr = fmt.get('abr', 0)  # audio bitrate
                    asr = fmt.get('asr', 0)  # audio sample rate
                    format_id = fmt.get('format_id', '')
                    
                    if not audio_format or abr > audio_format.get('abr', 0):
                        audio_format = {
                            'ext': fmt.get('ext', ''),
                            'abr': abr,
                            'asr': asr,
                            'format_id': format_id
                        }

            if audio_format:
                quality_str = f"{audio_format['abr']}k/{audio_format['asr']}Hz"
                format_str = f"{audio_format['ext']}"
            else:
                quality_str = "N/A"
                format_str = "N/A"

            return SearchResult(
                video_id=video_id,
                title=title,
                artist=artist,
                duration=duration_str,
                genre=genre,
                tags=tags[:3],
                thumbnail_url=entry.get('thumbnail'),
                audio_quality=quality_str,
                audio_format=format_str
            )
        except Exception as e:
            self.error_handler.warning(f"Chyba při extrakci informací o videu: {e}")
            return None