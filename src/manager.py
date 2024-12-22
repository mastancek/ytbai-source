from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path
import time
from rich.console import Console
import yt_dlp
from openai import OpenAI
import os
from utils import sanitize_filename, cleanup_thumbnail_cache
from rich.status import Status
from rich.text import Text
from dotenv import load_dotenv
from rich.prompt import Prompt
import cohere
import replicate
import requests
from utils import TokenCostCalculator
import json
from huggingface_hub import HfApi, InferenceClient
from rich.table import Table
import logging
from exceptions import ConfigError

@dataclass
class SearchResult:
    """Výsledek vyhledávání"""
    video_id: str
    title: str
    artist: str
    duration: str
    thumbnail_url: str = None
    
    @classmethod
    def from_youtube_item(cls, item: dict) -> 'SearchResult':
        """Vytvoří instanci z YouTube API výsledku"""
        # Získání délky videa
        duration_str = item.get('duration')
        if duration_str:
            # Převod ISO 8601 formátu na čitelný formát
            try:
                # Odstraníme 'PT' z začátku (např. 'PT3M24S')
                duration = duration_str[2:]
                hours = 0
                minutes = 0
                seconds = 0
                
                # Parsování hodin, minut a sekund
                if 'H' in duration:
                    hours, duration = duration.split('H')
                    hours = int(hours)
                if 'M' in duration:
                    minutes, duration = duration.split('M')
                    minutes = int(minutes)
                if 'S' in duration:
                    seconds = int(duration.rstrip('S'))
                
                # Formátování výsledku
                if hours > 0:
                    duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    duration = f"{minutes}:{seconds:02d}"
            except:
                duration = "0:00"
        else:
            duration = "0:00"

        return cls(
            video_id=item.get('id', {}).get('videoId', ''),
            title=item.get('snippet', {}).get('title', 'Neznámý název'),
            artist=item.get('snippet', {}).get('channelTitle', 'Neznámý interpret'),
            duration=duration,
            thumbnail_url=item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url')
        )

@dataclass
class DownloadContext:
    """Třída pro uchování kontextu posledního stahování"""
    downloaded_tracks: List[SearchResult]
    timestamp: float
    
    def is_valid(self) -> bool:
        """Kontrola, zda je kontext stále relevantní"""
        return time.time() - self.timestamp < 1800  # 30 minut

class PerplexityAPI:
    """Wrapper pro Perplexity API"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, prompt: str, model: str = "mixtral-8x7b-instruct") -> str:
        """Generování odpovědi pomocí Perplexity API"""
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a music expert that recommends songs."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 300,
            "temperature": 0.7,
            "top_p": 0.9
        }

        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        # Zpracování odpovědi podle dokumentace
        result = response.json()
        if result and "choices" in result:
            return result["choices"][0]["message"]["content"]
        raise Exception("Neplatná odpověď od API")

class HuggingFaceAPI:
    """Wrapper pro Hugging Face Inference API"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.api_url = "https://api-inference.huggingface.co/models"

    def generate(self, prompt: str, model: str = "facebook/opt-350m") -> str:
        """Generování odpovědi pomocí Hugging Face API"""
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7,
                "num_return_sequences": 1
            }
        }
        
        response = requests.post(
            f"{self.api_url}/{model}",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        return response.json()[0]["generated_text"]

class YTBAIManager:
    def __init__(self, project_root: Optional[Path] = None):
        """Inicializace manageru"""
        # Nejdřív inicializujeme console
        self.console = Console()
        
        # Pak nastavíme project_root
        self.project_root = project_root or Path(__file__).parent.parent
        
        # Načtení konfigurace
        self.config = self._load_config()
        
        # Načtení proměnných prostředí z .env souboru
        env_path = self.project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            self.console.print("[yellow]Soubor .env nenalezen, používám systémové proměnné[/yellow]")
        
        # Inicializace YouTube API klienta
        try:
            youtube_api_key = os.getenv('YOUTUBE_API_KEY')
            if youtube_api_key:
                from googleapiclient.discovery import build
                self.youtube = build(
                    'youtube', 
                    'v3',
                    developerKey=youtube_api_key
                )
                self.console.print("[green]YouTube API úspěšně inicializováno[/green]")
            else:
                self.console.print("[yellow]YouTube API klíč není nastaven v .env souboru[/yellow]")
                self.youtube = None
        except ImportError:
            self.console.print("[yellow]Chybí google-api-python-client, používám fallback na yt-dlp[/yellow]")
            self.youtube = None
        except Exception as e:
            self.console.print(f"[yellow]Chyba při inicializaci YouTube API: {e}[/yellow]")
            self.youtube = None
        
        # Inicializace OpenAI klienta
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
        else:
            self.openai_client = None
        
        self.current_context: Optional[DownloadContext] = None
        
        # Inicializace cache složky
        self.cache_dir = Path.home() / ".ytbai" / "cache" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Vyčištění starých náhledů při startu
        cleanup_thumbnail_cache(self.cache_dir)
        
        # Načteme API klíče a zkontrolujeme jejich dostupnost
        self.check_api_keys()
        
        # Inicializace dostupných AI služeb
        self._setup_clients()

    def _setup_clients(self):
        """Inicializace potřebných klientů"""
        ffmpeg_location = str(self.project_root / "bin" / "ffmpeg.exe")
        
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    # První postprocessor - extrakce audia
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    # Druhý postprocessor - normalizace hlasitosti
                    'key': 'FFmpegMetadata',
                },
                {
                    # Vlastní postprocessor pro normalizaci
                    'key': 'FFmpegPostProcessor',
                    'preferedformat': 'mp3',
                    # Dvouprůchodová normalizace pro lepší výsledek
                    'args': [
                        '-af',
                        'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json',
                        '-ar', '44100',  # Vzorkovací frekvence
                        '-metadata', 'comment=Normalized with FFmpeg loudnorm'
                    ],
                }
            ],
            'quiet': True,
            'no_warnings': True,
            'outtmpl': '%(title)s.%(ext)s',
            'paths': {
                'home': str(Path.home() / "Music" / "YouTube")
            },
            'ffmpeg_location': ffmpeg_location
        }
        
        self.search_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch10',
            'ffmpeg_location': ffmpeg_location,
            'ignoreerrors': True,
            'no_playlist': True,  # Ignorovat playlisty
            'extract_flat': 'in_playlist',
            'force_generic_extractor': False
        }

        # Inicializace Hugging Face klienta
        if os.getenv('HUGGINGFACE_API_KEY'):
            self.hf_api = HfApi(token=os.getenv('HUGGINGFACE_API_KEY'))
            self.text_generator = InferenceClient(
                model="gpt2",  # výchozí model
                token=os.getenv('HUGGINGFACE_API_KEY')
            )
        else:
            self.hf_api = None
            self.text_generator = None

        # Inicializace Cohere klienta s novým V2 API
        if os.getenv('COHERE_API_KEY'):
            self.co = cohere.ClientV2(os.getenv('COHERE_API_KEY'))
        else:
            self.co = None

        # Inicializace OpenAI klienta
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            # Použijeme model z konfigurace nebo výchozí
            self.openai_model = self.config.get('ai_services', {}).get('openai', {}).get('model', 'gpt-3.5-turbo')
            self.console.print(f"[green]OpenAI model: {self.openai_model}[/green]")
        else:
            self.openai_client = None
            self.openai_model = None

    def search_music(self, query: str, max_results: int = 10, use_youtube_ai: bool = False) -> List[SearchResult]:
        """Vyhledá hudbu na YouTube"""
        try:
            if self.youtube:
                try:
                    # Pokus o použití YouTube API
                    search_query = query
                    if not use_youtube_ai:
                        search_query += " music audio"

                    request = self.youtube.search().list(
                        q=search_query,
                        part="id,snippet",
                        maxResults=max_results,
                        type="video",
                        videoCategoryId="10"  # Kategorie Hudba
                    )
                    search_response = request.execute()
                    
                    # Získání ID videí pro další dotaz
                    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                    
                    # Získání detailů videí včetně délky
                    videos_request = self.youtube.videos().list(
                        id=','.join(video_ids),
                        part="contentDetails,snippet"
                    )
                    videos_response = videos_request.execute()
                    
                    # Vytvoření mapy délky videí
                    duration_map = {
                        item['id']: item['contentDetails']['duration']
                        for item in videos_response.get('items', [])
                    }
                    
                    # Přidání délky do výsledků vyhledávání
                    for item in search_response.get('items', []):
                        item['duration'] = duration_map.get(item['id']['videoId'], 'PT0M0S')

                    return [
                        SearchResult.from_youtube_item(item)
                        for item in search_response.get('items', [])
                    ]

                except Exception as e:
                    logging.warning(f"YouTube API selhalo: {e}, používám fallback na yt-dlp")
                    self.youtube = None  # Vypneme API pro další požadavky
            
            # Fallback na yt-dlp
            if not self.youtube:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'default_search': f'ytsearch{max_results}',
                    'ignoreerrors': True,
                    'no_playlist': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                    
                    if results and 'entries' in results:
                        return [
                            SearchResult(
                                video_id=entry['id'],
                                title=entry.get('title', 'Neznámý název'),
                                artist=entry.get('uploader', 'Neznámý interpret'),
                                duration=str(entry.get('duration_string', '0:00')),
                                thumbnail_url=entry.get('thumbnail')
                            )
                            for entry in results['entries']
                            if entry
                        ]

            return []

        except Exception as e:
            logging.error(f"Chyba při vyhledávání: {e}")
            return []

    def process_download(self, selections: List[SearchResult]) -> None:
        """Zpracování stahování"""
        downloaded = []
        base_dir = Path.home() / "Music" / "YouTube"
        
        # Získ��ní nastavení cover art
        cover_settings = self.config.get('download', {}).get('cover_art', {
            'enabled': True,
            'size': 1000,
            'format': 'jpg',
            'quality': 85
        })
        
        download_opts = {
            **self.ydl_opts,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'writethumbnail': cover_settings['enabled'],  # Stáhneme náhled jen pokud je povolený
            'outtmpl': str(base_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True
        }
        
        if cover_settings['enabled']:
            # Přidáme postprocessor pro úpravu náhledu
            download_opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False
            })

        genre_file = self.project_root / "data" / "genre_list.json"
        genre_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Načteme existující žánry
        genres = {}
        if genre_file.exists():
            with open(genre_file, 'r', encoding='utf-8') as f:
                genres = json.load(f)
        
        for selection in selections:
            try:
                url = f"https://www.youtube.com/watch?v={selection.video_id}"
                
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    # Nejdřív zjistíme, jestli je to playlist
                    info = ydl.extract_info(url, download=False)
                    
                    if info.get('_type') == 'playlist':
                        # Je to playlist - vytvoříme složku
                        playlist_title = sanitize_filename(info.get('title', 'Unknown Playlist'))
                        playlist_dir = base_dir / playlist_title
                        playlist_dir.mkdir(exist_ok=True)
                        
                        # Upravíme nastavení pro playlist
                        playlist_opts = {
                            **download_opts,
                            'outtmpl': str(playlist_dir / '%(title)s.%(ext)s')
                        }
                        
                        self.console.print(f"[yellow]Detekován playlist: {info.get('title')}[/yellow]")
                        self.console.print(f"[yellow]Počet skladeb: {info.get('playlist_count', 'neznámý')}[/yellow]")
                        
                        if Prompt.ask("Chcete stáhnout celý playlist? [y/n]", choices=['y', 'n']) == 'y':
                            with Status("[yellow]Stahuji playlist...[/yellow]", spinner="dots") as status:
                                with yt_dlp.YoutubeDL(playlist_opts) as playlist_dl:
                                    playlist_dl.download([url])
                                    
                                    # Přidáme všechny skladby do downloaded
                                    for entry in info.get('entries', []):
                                        if entry:
                                            result = SearchResult.from_ytdlp_result(entry)
                                            downloaded.append(result)
                                            status.update(f"[green]Staženo:[/green] {result.title}")
                    else:
                        # Je to jednotlivá skladba
                        self.console.print(f"[yellow]Stahuji: {selection.title}[/yellow]")
                        with yt_dlp.YoutubeDL(download_opts) as video_dl:
                            video_dl.download([url])
                        downloaded.append(selection)
                        self.console.print(f"[green]Úspěšně staženo: {selection.title}[/green]")
                
                # Získáme žánr z metadat
                genre = info.get('genre', 'Unknown')
                if genre != 'Unknown':
                    # Přidáme skladbu do seznamu žánrů
                    if genre not in genres:
                        genres[genre] = []
                    
                    song_info = {
                        'title': info.get('title', ''),
                        'artist': info.get('artist', ''),
                        'video_id': selection.video_id,
                        'downloaded': True
                    }
                    
                    # Přidáme pouze pokud tam ještě není
                    if not any(s['video_id'] == song_info['video_id'] for s in genres[genre]):
                        genres[genre].append(song_info)
            
            except Exception as e:
                self.console.print(f"[red]Chyba při stahování {selection.title}: {e}[/red]")
        
        # Uložíme aktualizovaný seznam žánrů
        with open(genre_file, 'w', encoding='utf-8') as f:
            json.dump(genres, f, indent=2, ensure_ascii=False)
        
        # Aktualizace kontextu pro doporučení
        if downloaded:
            self.current_context = DownloadContext(
                downloaded_tracks=downloaded,
                timestamp=time.time()
            )

    def get_recommendations(self, similar_to: List[SearchResult]) -> List[SearchResult]:
        """Získání doporučení na základě předchozích stažení"""
        recommendations = []
        seen_ids = set()  # Pro sledování již přidaných videí
        
        try:
            for track in similar_to[:3]:  # Bereme max 3 skladby jako základ
                # Různé způsoby hledání podobných skladeb
                search_queries = [
                    f"{track.artist} similar songs",  # Podobné skladby od stejného interpreta
                    f"songs like {track.title}",      # Podobné skladby podle názvu
                    f"mix {track.artist} {track.title}", # YouTube mix style
                    f"{track.artist} best songs",     # Nejlepší skladby od interpreta
                    f"if you like {track.title}"      # Doporučení stylem "pokud se vám líbí..."
                ]
                
                for query in search_queries:
                    if len(recommendations) >= 10:  # Max 10 doporučení celkem
                        break
                        
                    with yt_dlp.YoutubeDL(self.search_opts) as ydl:
                        self.console.print(f"[dim]Hledám podobné: {query}[/dim]")
                        results = ydl.extract_info(f"ytsearch3:{query}", download=False)
                        
                        if results and 'entries' in results:
                            for entry in results['entries']:
                                if not entry or entry.get('id') in seen_ids:
                                    continue
                                    
                                # Kontrola, zda nejde o původní skladbu
                                if entry.get('id') == track.video_id:
                                    continue
                                    
                                # Přidáme pouze pokud to je video (ne playlist) a není živé
                                if (entry.get('_type') == 'url' or entry.get('webpage_url_basename') == 'watch') \
                                   and not entry.get('is_live', False):
                                    try:
                                        video_info = ydl.extract_info(
                                            entry.get('url') or entry.get('id'),
                                            download=False
                                        )
                                        if video_info:
                                            result = SearchResult(
                                                title=video_info.get('title', 'Neznámý název'),
                                                artist=video_info.get('uploader', 'Neznámý autor'),
                                                duration=str(video_info.get('duration_string', '0:00')),
                                                video_id=video_info.get('id', ''),
                                                thumbnail_url=video_info.get('thumbnail', None)
                                            )
                                            recommendations.append(result)
                                            seen_ids.add(result.video_id)
                                            
                                            # Debug info
                                            self.console.print(
                                                f"[dim]Nalezeno podobné: {result.title} od {result.artist}[/dim]"
                                            )
                                    except Exception as e:
                                        self.console.print(f"[dim red]Chyba při zpracování doporučení: {e}[/dim red]")
                                        continue
                                
                                if len(recommendations) >= 10:
                                    break
                
            if not recommendations:
                self.console.print("[yellow]Nenalezena žádná podobná hudba[/yellow]")
            
            return recommendations
            
        except Exception as e:
            self.console.print(f"[red]Chyba při získávání doporučení: {e}[/red]")
            return [] 

    def get_ai_recommendations(self, mood_query: str = None) -> List[SearchResult]:
        """Získání AI doporučení s fallbackem a informacemi o průběhu"""
        try:
            # Nejdřív zjistíme dostupné služby
            available_services = []
            if os.getenv('OPENAI_API_KEY'):
                available_services.append(("OpenAI", self._get_openai_recommendations))
            if os.getenv('PERPLEXITY_API_KEY'):
                available_services.append(("Perplexity", self._get_perplexity_recommendations))
            if os.getenv('COHERE_API_KEY'):
                available_services.append(("Cohere", self._get_cohere_recommendations))
            if os.getenv('REPLICATE_API_TOKEN'):
                available_services.append(("Replicate", self._get_replicate_recommendations))
            if os.getenv('HUGGINGFACE_API_KEY'):
                available_services.append(("Hugging Face", self._get_huggingface_recommendations))

            if not available_services:
                self.console.print("[red]Žádná AI služba není dostupná![/red]")
                self.console.print("Nastavte alespoň jeden API klíč v souboru .env")
                return []

            # Zkusíme postupně všechny dostupné služby
            with Status("[yellow]Získávám AI doporučení...[/yellow]", spinner="dots") as status:
                for service_name, service_func in available_services:
                    try:
                        status.update(f"[yellow]Používám službu {service_name}...[/yellow]")
                        results = service_func(mood_query)
                        if results:
                            status.update(f"[green]Úspěšně získána doporučení od {service_name}[/green]")
                            return results
                        else:
                            status.update(f"[yellow]{service_name} nevrátil žádné výsledky, zkouším další...[/yellow]")
                    except Exception as e:
                        status.update(f"[yellow]{service_name} selhal ({str(e)}), zkouším další...[/yellow]")
                        continue

            self.console.print("[red]Všechny dostupné AI služby selhaly[/red]")
            return []

        except Exception as e:
            self.console.print(f"[red]Chyba při získávání AI doporučení: {e}[/red]")
            return []

    def get_ai_conversation_results(self, query: str) -> List[SearchResult]:
        """Zpracování konverzace s AI a získání doporučení"""
        try:
            prompt = f"""
            Uživatel se ptá na hudbu: {query}
            Odpověz jako hudební expert a navrhni 5 konkrétních skladeb.
            Odpověz ve formátu:
            ODPOVĚĎ: Tvoje odpověď na otázku...
            DOPORUČENÍ:
            1. Interpret - Název skladby
            2. Interpret - Název skladby
            ...
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Jsi hudební expert se znalostí všech žánrů a období."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Rozdělení odpovědi na text a doporučení
            content = response.choices[0].message.content
            parts = content.split("DOPORUČENÍ:")
            
            if len(parts) > 1:
                self.console.print(f"[green]{parts[0].replace('ODPOVĚĎ:', '').strip()}[/green]")
                suggestions = parts[1].strip().split('\n')
                return self._process_ai_suggestions(suggestions)
            
            return []
            
        except Exception as e:
            self.console.print(f"[red]Chyba při komunikaci s AI: {e}[/red]")
            return []

    def get_ai_mood_results(self, mood: str) -> List[SearchResult]:
        """Získání doporučení podle nálady/aktivity"""
        try:
            prompt = f"""
            Uživatel hledá hudbu pro: {mood}
            Navrhni 5 perfektních skladeb pro tuto aktivitu/náladu.
            Vysvětli krátce proč jsou vhodné a uveď je ve formátu:
            VYSVĚTLENÍ: Tvoje vysvětlení...
            SKLADBY:
            1. Interpret - Název skladby
            2. Interpret - Název skladby
            ...
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Jsi hudební expert, který doporučuje skladby podle nálady a aktivity."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            parts = content.split("SKLADBY:")
            
            if len(parts) > 1:
                if "VYSVĚTLENÍ:" in parts[0]:
                    self.console.print(f"[green]{parts[0].replace('VYSVĚTLENÍ:', '').strip()}[/green]")
                suggestions = parts[1].strip().split('\n')
                return self._process_ai_suggestions(suggestions)
            
            return []
            
        except Exception as e:
            self.console.print(f"[red]Chyba při získávání doporučení podle nálady: {e}[/red]")
            return []

    def get_ai_explorer_results(self, category: str) -> List[SearchResult]:
        """Průzkum hudby podle kategorie"""
        try:
            prompt = f"""
            Uživatel chce prozkoumat: {category}
            Navrhni 5 reprezentativních nebo zajímavých skladeb z této kategorie.
            Přidej krátký popis každé skladby a její význam.
            Odpověz ve formátu:
            ÚVOD: Krátký úvod do kategorie...
            SKLADBY:
            1. Interpret - Název skladby
               Popis: Proč je skladba významná...
            2. Interpret - Název skladby
               Popis: Proč je skladba významná...
            ...
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Jsi hudební historik a expert se znalostí všech žánrů a období."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            parts = content.split("SKLADBY:")
            
            if len(parts) > 1:
                if "ÚVOD:" in parts[0]:
                    self.console.print(f"[green]{parts[0].replace('ÚVOD:', '').strip()}[/green]")
                
                suggestions = []
                current_song = None
                
                for line in parts[1].strip().split('\n'):
                    if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                        if current_song:
                            suggestions.append(current_song)
                        current_song = line.strip()
                    elif line.strip().startswith('Popis:') and current_song:
                        self.console.print(f"[dim]{line.strip()}[/dim]")
                
                if current_song:
                    suggestions.append(current_song)
                    
                return self._process_ai_suggestions(suggestions)
            
            return []
            
        except Exception as e:
            self.console.print(f"[red]Chyba při průzkumu hudby: {e}[/red]")
            return []

    def _process_ai_suggestions(self, suggestions: List[str]) -> List[SearchResult]:
        """Zpracování návrhů od AI a vyhledání na YouTube"""
        results = []
        
        with Status("[yellow]Vyhledávám doporučené skladby na YouTube...[/yellow]", spinner="dots") as status:
            for suggestion in suggestions:
                if not suggestion.strip():
                    continue
                
                # Očistíme formátování od AI
                suggestion = suggestion.strip()
                if '. ' in suggestion:  # Odstraníme číslování (např. "1. ")
                    suggestion = suggestion.split('. ', 1)[1]
                
                # Kontrola formátu "Artist - Title"
                if ' - ' not in suggestion:
                    continue
                    
                artist, title = suggestion.split(' - ', 1)
                artist = artist.strip()
                title = title.strip()
                
                status.update(f"[yellow]Hledám: {artist} - {title}[/yellow]")
                
                # Vyhledání na YouTube
                search_query = f"{artist} {title} official"
                with yt_dlp.YoutubeDL(self.search_opts) as ydl:
                    try:
                        video_results = ydl.extract_info(
                            f"ytsearch1:{search_query}", 
                            download=False
                        )
                        
                        if video_results and 'entries' in video_results:
                            entries = [e for e in video_results['entries'] if e]
                            if entries:
                                entry = entries[0]
                                # Kontrola délky (ignorujeme příliš dlouhé/krátké)
                                duration = entry.get('duration', 0)
                                if 60 <= duration <= 600:  # mezi 1-10 minutami
                                    result = SearchResult(
                                        title=title,  # Použijeme původní název od AI
                                        artist=artist,  # Použijeme původního interpreta od AI
                                        duration=str(entry.get('duration_string', '0:00')),
                                        video_id=entry.get('id', ''),
                                        thumbnail_url=entry.get('thumbnail', None)
                                    )
                                    results.append(result)
                                    status.update(f"[green]Nalezeno: {artist} - {title}[/green]")
                                else:
                                    status.update(f"[yellow]Přeskakuji: {artist} - {title} (nevhodná délka)[/yellow]")
                    except Exception as e:
                        status.update(f"[red]Nelze najít: {artist} - {title} ({str(e)})[/red]")
                        continue
        
        if not results:
            self.console.print("[yellow]Varování: Žádné z AI doporučení nebylo nalezeno na YouTube[/yellow]")
        
        return results

    def _get_openai_recommendations(self, query: str) -> List[SearchResult]:
        """Získá doporučení od OpenAI"""
        if not self.openai_client or not self.openai_model:
            raise ConfigError("OpenAI není nakonfigurováno")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": """Jsi hudební expert. 
                    Při doporučování NEPŘEKLÁDEJ názvy skladeb a interpretů do češtiny.
                    Zachovej původní anglické názvy."""},
                    {"role": "user", "content": f"Doporuč 5 skladeb pro: {query}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            recommendations = response.choices[0].message.content
            return self._process_ai_suggestions(recommendations)
            
        except Exception as e:
            raise ConfigError(f"Chyba OpenAI API: {str(e)}")

    def _get_cohere_recommendations(self, mood_query: str) -> List[SearchResult]:
        """Získání doporučení pomocí Cohere API"""
        try:
            response = self.co.chat(
                message=f"""Doporuč 5 skladeb pro náladu: {mood_query}
                Odpověz ve formátu:
                1. "Název skladby" od Interpret - zdůvodnění
                2. "Název skladby" od Interpret - zdůvodnění
                """,
                model="command",
                temperature=0.7
            )
            return self._process_ai_suggestions(response.text)
        except Exception as e:
            raise ConfigError(f"Chyba Cohere API: {str(e)}")

    def _get_replicate_recommendations(self, mood_query: str) -> List[SearchResult]:
        """Získání doporučení pomocí Replicate"""
        try:
            output = self.replicate.run(
                "replicate/llama-2-70b-chat:2796ee9483c3fd7aa2e171d38f4ca12251a30609463dcfd4cd76703f22e96cdf",
                input={
                    "prompt": f"""Recommend 5 songs for {mood_query} mood.
                    Format each recommendation as: Artist - Song Title
                    Example:
                    1. The Beatles - Hey Jude"""
                }
            )
            suggestions = output.split('\n')
            return self._process_ai_suggestions(suggestions)
        except Exception as e:
            raise Exception(f"Replicate error: {e}")

    def _get_perplexity_recommendations(self, mood_query: str) -> List[SearchResult]:
        """Získání doporučení pomocí Perplexity"""
        try:
            prompt = f"""
            Recommend 5 songs for {mood_query} mood.
            Format each recommendation as: Artist - Song Title
            Example:
            1. The Beatles - Hey Jude
            2. Queen - Bohemian Rhapsody
            """
            
            response = self.perplexity.generate(prompt)
            suggestions = [
                line.strip() for line in response.split('\n')
                if line.strip() and ' - ' in line
            ]
            
            return self._process_ai_suggestions(suggestions)
        except Exception as e:
            raise Exception(f"Perplexity error: {e}")

    def _get_huggingface_recommendations(self, mood_query: str) -> List[SearchResult]:
        try:
            response = self.text_generator(
                f"Doporuč 5 skladeb pro náladu: {mood_query}",
                max_length=200,
                num_return_sequences=1
            )
            text = response[0]['generated_text']
            return self._process_ai_suggestions(text)
        except Exception as e:
            raise ConfigError(f"Chyba Hugging Face API: {str(e)}")

    def check_api_keys(self) -> None:
        """Kontrola dostupnosti API klíčů a zobrazení instrukcí pro registraci"""
        missing_keys = []
        
        # OpenAI
        if not os.getenv('OPENAI_API_KEY'):
            missing_keys.append(
                "[yellow]OpenAI API[/yellow] (Placené)\n"
                "1. Registrujte se na [link]https://platform.openai.com[/link]\n"
                "2. Přejděte do API keys sekce\n"
                "3. Vytvořte nový API klíč\n"
                "4. Vložte klíč do .env: OPENAI_API_KEY=your-key-here\n"
            )
        
        # Cohere
        if not os.getenv('COHERE_API_KEY'):
            missing_keys.append(
                "[yellow]Cohere API[/yellow] (Free tier - 5M tokenů/měsíc)\n"
                "1. Registrujte se na [link]https://cohere.ai[/link]\n"
                "2. Přejděte do Dashboard -> API Keys\n"
                "3. Vytvořte nový API klíč\n"
                "4. Vložte klíč do .env: COHERE_API_KEY=your-key-here\n"
            )
        
        # Replicate
        if not os.getenv('REPLICATE_API_TOKEN'):
            missing_keys.append(
                "[yellow]Replicate API[/yellow] (Free credits)\n"
                "1. Registrujte se na [link]https://replicate.com[/link]\n"
                "2. Přejděte do Account Settings\n"
                "3. Vytvořte nový API token\n"
                "4. Vložte token do .env: REPLICATE_API_TOKEN=your-token-here\n"
            )
        
        if missing_keys:
            self.console.print("\n[bold red]Chybějící API klíče:[/bold red]")
            self.console.print(
                "[dim]Pro využití AI funkcí je potřeba alespoň jeden API klíč.[/dim]\n"
                "[dim]Doporučujeme začít s bezplatnými službami (Hugging Face, Cohere, Perplexity).[/dim]\n"
            )
            for key_info in missing_keys:
                self.console.print(key_info + "\n")

    def _get_ai_recommendations(self, mood_query: str, provider: str) -> List[SearchResult]:
        """Získání doporučení od AI s strukturovaným formátem"""
        
        # Strukturovaný prompt pro všechny AI služby
        structured_prompt = {
            "task": "music_recommendation",
            "input": {
                "mood": mood_query,
                "count": 5,
                "format": "json",
                "required_fields": ["artist", "title", "genre", "mood_match", "description"]
            },
            "instructions": """
            Please recommend 5 songs that match the given mood.
            Return ONLY valid JSON without any additional text.
            Example format:
            {
                "recommendations": [
                    {
                        "artist": "The Beatles",
                        "title": "Here Comes the Sun",
                        "genre": "Rock",
                        "mood_match": "Uplifting and bright melody perfect for happy mood",
                        "description": "Classic feel-good song with positive vibes"
                    }
                ]
            }
            """
        }

        prompt = json.dumps(structured_prompt, indent=2)
        
        try:
            # Výpočet předpokládané ceny
            cost_estimate = TokenCostCalculator.calculate_cost(prompt, "", provider)
            self.console.print(
                f"[dim]Předpokládaná cena ({provider}): "
                f"{cost_estimate['total_cost_czk']:.2f} Kč[/dim]"
            )
            
            # Získání odpovědi podle poskytovatele
            if provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a music expert. Always respond in the requested JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ "type": "json_object" }
                )
                content = response.choices[0].message.content
                
            elif provider == "cohere":
                response = self.co.generate(
                    model='command',
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.7,
                    response_format="json"
                )
                content = response.generations[0].text
                
            else:
                raise ValueError(f"Nepodporovaný poskytovatel: {provider}")
                
            # Výpočet skutečné ceny
            actual_cost = TokenCostCalculator.calculate_cost(prompt, content, provider)
            self.console.print(
                f"[dim]Skutečná cena ({provider}): {actual_cost['total_cost_czk']:.2f} Kč "
                f"[Tokeny: {actual_cost['total_tokens']}][/dim]"
            )
            
            # Parsování JSON odpovědi
            try:
                data = json.loads(content)
                recommendations = data.get("recommendations", [])
                
                # Zobrazíme přehlednou tabulku doporučení
                table = Table(show_header=True)
                table.add_column("č.", justify="right", style="cyan")
                table.add_column("Interpret", style="green")
                table.add_column("Skladba", style="white")
                table.add_column("Žánr", style="yellow")
                table.add_column("Proč se hodí", style="blue", max_width=40)
                
                for i, rec in enumerate(recommendations, 1):
                    table.add_row(
                        str(i),
                        rec['artist'],
                        rec['title'],
                        rec['genre'],
                        rec['mood_match']
                    )
                
                self.console.print("\n[bold]Doporučené skladby:[/bold]")
                self.console.print(table)
                
                # Převod na SearchResult objekty pro vyhledání na YouTube
                suggestions = [
                    f"{rec['artist']} - {rec['title']}"
                    for rec in recommendations
                ]
                
                # Vyhledáme skladby na YouTube
                with Status("[yellow]Hledám doporučené skladby na YouTube...[/yellow]", spinner="dots"):
                    return self._process_ai_suggestions(suggestions)
                    
            except json.JSONDecodeError:
                raise Exception(f"Neplatný JSON formát odpovědi od {provider}")
                
        except Exception as e:
            raise Exception(f"{provider} error: {str(e)}")

    def get_ai_recommendations(self, track: SearchResult) -> List[SearchResult]:
        """Získání doporučení pomocí Hugging Face modelu"""
        try:
            # Sestavení promptu
            prompt = f"""Doporuč podobné skladby k:
            Interpret: {track.artist}
            Název: {track.title}
            """
            
            # Nová syntaxe pro generování
            response = self.text_generator.text_generation(
                prompt,
                max_new_tokens=200,
                num_return_sequences=3,
                temperature=0.7,
                do_sample=True
            )
            
            # Zpracování odpovědi
            recommendations = []
            if isinstance(response, list):
                for generation in response:
                    try:
                        parsed = self._parse_recommendation(generation.generated_text)
                        if parsed:
                            recommendations.append(parsed)
                    except Exception as e:
                        self.console.print(f"[yellow]Chyba při zpracování doporučení: {e}[/yellow]")
            else:
                parsed = self._parse_recommendation(response.generated_text)
                if parsed:
                    recommendations.append(parsed)
            
            return recommendations
            
        except Exception as e:
            self.console.print(f"[red]Chyba při získávání doporučení: {e}[/red]")
            return []

    def _parse_recommendation(self, text: str) -> Optional[SearchResult]:
        """Pomocná metoda pro parsování doporučení z AI"""
        try:
            # Implementace parsování textu na SearchResult
            # Toto je třeba přizpůsobit formátu odpovědi od konkrétního modelu
            pass
        except:
            return None

    def get_available_models(self, service: str) -> List[Dict[str, Any]]:
        """Získá seznam dostupných modelů pro danou službu"""
        try:
            if service == "openai" and self.openai_client:
                # OpenAI API
                models = self.openai_client.models.list()
                return [
                    {
                        "id": model.id,
                        "name": model.id,
                        "description": "GPT model"
                    }
                    for model in models.data
                    if any(name in model.id for name in ['gpt-3.5', 'gpt-4'])
                ]
                
            elif service == "huggingface" and self.hf_api:
                # Hugging Face API - získá populární modely pro generování textu
                models = self.hf_api.list_models(
                    filter={"task": "text-generation"},  # Opravený filtr
                    sort="downloads",
                    direction=-1,
                    limit=10
                )
                return [
                    {
                        "id": model.modelId,  # Opravený přístup k ID
                        "name": model.modelId,
                        "description": getattr(model, 'description', 'Není k dispozici'),
                        "downloads": getattr(model, 'downloads', 0)
                    }
                    for model in models
                ]
                
            elif service == "cohere" and self.co:
                # Cohere API v2 - fixní seznam dostupných modelů
                models = [
                    {
                        "id": "command",
                        "name": "Command",
                        "description": "Nejnovější stabilní verze"
                    },
                    {
                        "id": "command-light",
                        "name": "Command Light",
                        "description": "Rychlejší a levnější verze"
                    },
                    {
                        "id": "command-nightly",
                        "name": "Command Nightly",
                        "description": "Nejnovější experimentální verze"
                    },
                    {
                        "id": "command-r",
                        "name": "Command-R",
                        "description": "Vylepšená verze s lepším reasoningem"
                    }
                ]
                return models
                
            elif service == "replicate" and self.replicate:
                # Replicate API - vrátí populární LLM modely
                models = [
                    {
                        "id": "meta/llama-2-70b-chat",
                        "name": "Llama 2 70B",
                        "description": "Největší veřejně dostupný chatovací model"
                    },
                    {
                        "id": "meta/llama-2-13b-chat",
                        "name": "Llama 2 13B",
                        "description": "Střední velikost, dobrý poměr výkon/cena"
                    }
                ]
                return models
                
            return []
            
        except Exception as e:
            self.console.print(f"[yellow]Chyba při získávání modelů pro {service}: {e}[/yellow]")
            return []

    def search_single_track(self, query: str) -> Optional[SearchResult]:
        """Vyhledá jednu konkrétní skladbu na YouTube"""
        try:
            # Použijeme yt-dlp pro přesné vyhledání
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': 'ytsearch1',  # Hledáme pouze jeden výsledek
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch1:{query}", download=False)
                
                if result and 'entries' in result and result['entries']:
                    entry = result['entries'][0]
                    return SearchResult(
                        video_id=entry['id'],
                        title=entry.get('title', 'Neznámý název'),
                        artist=entry.get('uploader', 'Neznámý interpret'),
                        duration=str(entry.get('duration_string', '0:00')),
                        thumbnail_url=entry.get('thumbnail')
                    )
            return None
            
        except Exception as e:
            logging.error(f"Chyba při vyhledávání skladby: {e}")
            return None

    def _check_ollama_server(self) -> bool:
        """Kontrola dostupnosti Ollama serveru"""
        try:
            # Nejdřív zkusíme health check
            response = requests.get('http://localhost:11434/api/health', timeout=2)
            if response.status_code != 200:
                return False
            
            # Pak zkontrolujeme dostupné modely
            response = requests.get('http://localhost:11434/api/tags')
            models = response.json().get('models', [])
            
            # Zkontrolujeme dostupnost některého z podporovaných modelů
            supported_models = ['llama3.2', 'llama2', 'mistral', 'gemma2']
            return any(m.get('name') in supported_models for m in models)
            
        except Exception as e:
            self.console.print(f"[yellow]Chyba při kontrole Ollama serveru: {e}[/yellow]")
            return False

    def _get_ollama_recommendations(self, query: str) -> List[SearchResult]:
        """Získá doporučení od Ollama"""
        if not self._check_ollama_server():
            raise ConfigError("""
[red]Ollama není správně nastavena![/red]

Pro zprovoznění Ollama:

1. Stáhněte a nainstalujte Ollama:
   - Windows: https://ollama.ai/download/windows
   - Linux: curl -fsSL https://ollama.ai/install.sh | bash
   
2. Otevřete nový terminál a spusťte:
   [green]ollama serve[/green]
   
3. Stáhněte některý z doporučených modelů:
   [green]ollama pull llama3.2[/green]    # Nejnovější model (doporučeno)
   [green]ollama pull mistral[/green]     # Menší a rychlejší model
   [green]ollama pull gemma2[/green]      # Google Gemma 2 model
   
4. Počkejte na dokončení stahování modelu
   
[yellow]Tip: Pro nejlepší výkon doporučujeme model llama3.2[/yellow]
""")

        try:
            # Vylepšený prompt pro přesnější výsledky
            prompt = f"""Jsi hudební expert. Doporuč 5 skladeb pro: {query}

DŮLEŽITÉ INSTRUKCE:
- Zachovej PŘESNĚ původní názvy skladeb a interpretů v angličtině
- NEPŘEKLÁDEJ názvy do češtiny
- U každé skladby uveď žánr a krátké zdůvodnění v češtině
- Dodržuj přesně tento formát:

1. "PŮVODNÍ_NÁZEV_SKLADBY" od PŮVODNÍ_JMÉNO_INTERPRETA
   Žánr: ŽÁNR
   Důvod: KRÁTKÉ_ZDŮVODNĚNÍ

... atd.

Příklad:
1. "Master of Puppets" od Metallica
   Žánr: Thrash Metal
   Důvod: Technicky propracovaná skladba s agresivními riffy

Odpověz POUZE v tomto formátu, bez dalšího textu."""

            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama2',
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.7,
                    'top_p': 0.9
                },
                timeout=30
            )
            response.raise_for_status()
            
            recommendations = response.json().get('response', '')
            if not recommendations:
                raise ConfigError("Ollama nevrátila žádná doporučení")
            
            # Debug výpis pro kontrolu formátu
            self.console.print(f"[dim]Ollama response: {recommendations}[/dim]")
            
            # Extrakce skladeb z odpovědi
            songs = []
            current_song = {}
            
            for line in recommendations.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Detekce nové skladby (začíná číslem)
                if line[0].isdigit() and '"' in line and ' od ' in line:
                    if current_song:
                        songs.append(current_song)
                    current_song = {}
                    
                    # Extrakce názvu a interpreta
                    try:
                        title = line.split('"')[1]
                        artist = line.split(' od ')[1].split('   ')[0].strip()
                        current_song = {'title': title, 'artist': artist}
                        self.console.print(f"[dim]Nalezena skladba: {title} - {artist}[/dim]")
                    except:
                        continue
                
                # Přidání žánru a důvodu
                elif current_song:
                    if line.startswith('Žánr:'):
                        current_song['genre'] = line.replace('Žánr:', '').strip()
                    elif line.startswith('Důvod:'):
                        current_song['reason'] = line.replace('Důvod:', '').strip()
            
            # Přidání poslední skladby
            if current_song:
                songs.append(current_song)
            
            # Vyhledání skladeb na YouTube
            results = []
            with Status("[yellow]Vyhledávám doporučené skladby na YouTube...[/yellow]", spinner="dots"):
                for song in songs:
                    try:
                        # Vyhledání na YouTube
                        search_results = self.search_music(f"{song['title']} {song['artist']}")
                        if search_results:
                            result = search_results[0]
                            # Přidáme dodatečné informace
                            setattr(result, 'genre', song.get('genre', ''))
                            setattr(result, 'reason', song.get('reason', ''))
                            results.append(result)
                            self.console.print(f"[green]✓[/green] {song['title']} - {song['artist']}")
                        else:
                            self.console.print(f"[red]✗[/red] Nenalezeno: {song['title']} - {song['artist']}")
                    except Exception as e:
                        self.console.print(f"[red]Chyba při vyhledávání: {e}[/red]")
                        continue
            
            if not results:
                self.console.print("[yellow]Varování: Žádné z Ollama doporučení nebylo nalezeno na YouTube[/yellow]")
            
            return results
            
        except Exception as e:
            raise ConfigError(f"[red]Chyba při komunikaci s Ollama: {str(e)}[/red]")

    def _load_config(self) -> Dict[str, Any]:
        """Načte konfiguraci"""
        config_file = self.project_root / "config" / "config.json"
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Výchozí konfigurace
            default_config = {
                'paths': {
                    'music_dir': str(Path.home() / "Music" / "YouTube"),
                    'cache_dir': str(Path.home() / ".ytbai" / "cache"),
                    'logs_dir': str(Path.home() / ".ytbai" / "logs")
                },
                'download': {
                    'format': 'mp3',
                    'quality': '192k',
                    'max_concurrent': 3,
                    'cover_art': {
                        'enabled': True,
                        'size': 1000,
                        'format': 'jpg',
                        'quality': 85
                    }
                }
            }
            
            # Vytvoříme složky
            for path in default_config['paths'].values():
                Path(path).mkdir(parents=True, exist_ok=True)
                
            # Uložme výchozí konfiguraci
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
                
            return default_config
            
        except Exception as e:
            self.console.print(f"[yellow]Chyba při načítání konfigurace: {e}[/yellow]")
            return {}

    def _get_openai_credit(self) -> Optional[Dict[str, float]]:
        """Získá zbývající kredit na OpenAI účtu"""
        try:
            # Použijeme nové API endpointy pro billing
            response = requests.get(
                "https://api.openai.com/v1/usage",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Vrátí kredit v USD a CZK
            total_usage = data.get('total_usage', 0) / 100  # Převod na USD
            return {
                'usd': total_usage,
                'czk': total_usage * 24.0  # Přibližný kurz
            }
        except Exception as e:
            self.console.print(f"[yellow]Nepodařilo se získat informace o kreditu: {e}[/yellow]")
            return None

SUPPORTED_MODELS = {
    'llama3.2': {
        'name': 'Llama 3.2',
        'description': 'Nejnovější a nejlepší model',
        'size': '70B',
        'recommended': True
    },
    'mistral': {
        'name': 'Mistral',
        'description': 'Rychlý a efektivní model',
        'size': '7B',
        'recommended': True
    },
    'gemma2': {
        'name': 'Gemma 2',
        'description': 'Google Gemma 2 model',
        'size': '9B',
        'recommended': True
    }
}