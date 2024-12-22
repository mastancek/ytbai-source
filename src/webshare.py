from pathlib import Path
import requests
from typing import Optional, Dict, List
from rich.progress import Progress
import json
from exceptions import ConfigError

class WebshareDownloader:
    """Třída pro stahování z Webshare"""
    
    BASE_URL = "https://webshare.cz/"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None
        self._login()

    def _login(self) -> None:
        """Přihlášení do Webshare"""
        try:
            data = {
                "username_or_email": self.username,
                "password": self.password,
                "keep_logged_in": 1,
                "wst": ""
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Origin': 'https://webshare.cz',
                'Referer': 'https://webshare.cz/login/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Nejdřív získáme CSRF token
            response = self.session.get(f"{self.BASE_URL}login/")
            response.raise_for_status()
            
            # Přidáme cookies ze session do dalšího requestu
            response = self.session.post(
                f"{self.BASE_URL}api/login/",
                data=data,
                headers=headers
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response text: {response.text[:200]}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                raise ConfigError(f"Neplatná odpověď od serveru: {response.text[:200]}")
                
            if data.get("status") == "error":
                raise ConfigError(data.get("message", "Přihlášení selhalo"))
                
            self.token = data.get("token")
            if not self.token:
                raise ConfigError("Přihlášení selhalo - chybí token")
                
            # Uložíme token do session
            self.session.cookies.set('wst', self.token)
                
        except requests.RequestException as e:
            raise ConfigError(f"Chyba při komunikaci s Webshare: {str(e)}")

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Vyhledávání audio souborů"""
        try:
            response = self.session.post(
                f"{self.BASE_URL}search/",
                data={
                    "what": query,
                    "offset": 0,
                    "limit": limit,
                    "sort": "rating",
                    "type": "audio",
                    "wst": self.token
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "error":
                raise ConfigError(data.get("message", "Vyhledávání selhalo"))
                
            return data.get("files", [])
            
        except requests.RequestException as e:
            raise ConfigError(f"Chyba při vyhledávání: {str(e)}")

    def get_download_link(self, ident: str) -> str:
        """Získání odkazu ke stažení"""
        try:
            response = self.session.post(
                f"{self.BASE_URL}file_link/",
                data={
                    "ident": ident,
                    "wst": self.token
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "error":
                raise ConfigError(data.get("message", "Získání odkazu selhalo"))
                
            return data.get("link")
            
        except requests.RequestException as e:
            raise ConfigError(f"Chyba při získávání odkazu: {str(e)}")

    def download_file(self, ident: str, output_dir: Path) -> Path:
        """Stažení souboru s progress barem"""
        try:
            download_link = self.get_download_link(ident)
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Stahuji z Webshare...", total=100)
                
                response = self.session.get(download_link, stream=True)
                response.raise_for_status()
                
                # Získání názvu souboru
                filename = None
                content_disposition = response.headers.get('content-disposition')
                if content_disposition and 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                if not filename:
                    filename = f"webshare_{ident}.mp3"
                
                file_path = output_dir / filename
                file_size = int(response.headers.get('content-length', 0))
                
                # Stažení souboru po částech
                with open(file_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if file_size:
                                progress.update(task, completed=(downloaded / file_size) * 100)
                
                return file_path
                
        except Exception as e:
            raise ConfigError(f"Chyba při stahování: {str(e)}")

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Formátuje velikost souboru"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB" 