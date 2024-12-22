from typing import Optional, Dict
import json
from pathlib import Path
import yt_dlp
from rich.console import Console
from rich.prompt import Prompt
from .exceptions import AuthError

class YouTubeAuth:
    """Správce autentizace pro YouTube"""
    def __init__(self, config_dir: Path):
        self.console = Console()
        self.config_dir = config_dir
        self.credentials_file = config_dir / "youtube_credentials.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def login(self) -> Dict[str, str]:
        """Přihlášení k YouTube účtu pomocí přihlašovacích údajů"""
        try:
            if not self.credentials_file.exists():
                self.console.print("[yellow]Přihlášení k YouTube účtu[/yellow]")
                username = Prompt.ask("Zadejte email")
                password = Prompt.ask("Zadejte heslo", password=True)
                
                credentials = {
                    "username": username,
                    "password": password
                }
                
                # Uložení přihlašovacích údajů
                with open(self.credentials_file, 'w', encoding='utf-8') as f:
                    json.dump(credentials, f)
            else:
                # Načtení uložených přihlašovacích údajů
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    credentials = json.load(f)

            return credentials
            
        except Exception as e:
            raise AuthError(f"Chyba při přihlašování: {str(e)}")

    def get_playlists(self) -> list:
        """Získá seznam playlistů přihlášeného uživatele"""
        try:
            ydl_opts = {
                **self.login(),
                'extract_flat': True,
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Získání playlistů z kanálu uživatele
                result = ydl.extract_info(
                    "https://www.youtube.com/feed/library",
                    download=False
                )
                
                if 'entries' in result:
                    return [
                        {
                            'id': entry['id'],
                            'title': entry['title'],
                            'url': entry['url'],
                            'video_count': entry.get('video_count', 0)
                        }
                        for entry in result['entries']
                        if entry['_type'] == 'playlist'
                    ]
                return []
                
        except Exception as e:
            raise AuthError(f"Chyba při získávání playlistů: {str(e)}")

    def get_playlist_videos(self, playlist_url: str) -> list:
        """Získá seznam videí z playlistu"""
        try:
            ydl_opts = {
                **self.login(),
                'extract_flat': True,
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(playlist_url, download=False)
                
                if 'entries' in result:
                    return [
                        {
                            'id': entry['id'],
                            'title': entry['title'],
                            'duration': entry.get('duration', 0),
                            'uploader': entry.get('uploader', 'Unknown')
                        }
                        for entry in result['entries']
                        if entry is not None
                    ]
                return []
                
        except Exception as e:
            raise AuthError(f"Chyba při získávání videí z playlistu: {str(e)}")

    def logout(self) -> None:
        """Odhlášení - smaže uložené přihlašovací údaje"""
        try:
            if self.credentials_file.exists():
                self.credentials_file.unlink()
            self.console.print("[green]Úspěšně odhlášeno[/green]")
        except Exception as e:
            raise AuthError(f"Chyba při odhlašování: {str(e)}") 