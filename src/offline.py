from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from .exceptions import ValidationError
from .cache import Cache

@dataclass
class OfflineContent:
    """Reprezentace offline obsahu"""
    video_id: str
    title: str
    artist: str
    file_path: str
    downloaded_at: str
    size_bytes: int
    duration: str

class OfflineManager:
    """Správce offline obsahu"""
    def __init__(self, offline_dir: Path, cache: Cache):
        self.offline_dir = offline_dir
        self.offline_dir.mkdir(parents=True, exist_ok=True)
        self.cache = cache
        self.index_file = self.offline_dir / "offline_index.json"
        self.offline_content: Dict[str, OfflineContent] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Načte index offline obsahu"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.offline_content = {
                        vid: OfflineContent(**content)
                        for vid, content in data.items()
                    }
        except Exception as e:
            logging.error(f"Chyba při načítání offline indexu: {e}")

    def _save_index(self) -> None:
        """Uloží index offline obsahu"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                data = {
                    vid: asdict(content)
                    for vid, content in self.offline_content.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Chyba při ukládání offline indexu: {e}")

    def add_offline_content(self, content: OfflineContent) -> None:
        """Přidá obsah do offline módu"""
        self.offline_content[content.video_id] = content
        self._save_index()

    def remove_offline_content(self, video_id: str) -> None:
        """Odebere obsah z offline módu"""
        if video_id in self.offline_content:
            content = self.offline_content[video_id]
            try:
                # Odstranění souboru
                Path(content.file_path).unlink(missing_ok=True)
                # Odstranění z indexu
                del self.offline_content[video_id]
                self._save_index()
            except Exception as e:
                logging.error(f"Chyba při odstraňování offline obsahu: {e}")

    def get_offline_content(self, video_id: str) -> Optional[OfflineContent]:
        """Získá offline obsah podle ID"""
        return self.offline_content.get(video_id)

    def list_offline_content(self) -> List[OfflineContent]:
        """Vrátí seznam všeho offline obsahu"""
        return list(self.offline_content.values())

    def cleanup_old_content(self, max_age_days: int = 30) -> None:
        """Vyčistí starý offline obsah"""
        now = datetime.now()
        to_remove = []
        
        for video_id, content in self.offline_content.items():
            downloaded_at = datetime.fromisoformat(content.downloaded_at)
            if (now - downloaded_at) > timedelta(days=max_age_days):
                to_remove.append(video_id)
                
        for video_id in to_remove:
            self.remove_offline_content(video_id)

    def get_offline_size(self) -> int:
        """Vrátí celkovou velikost offline obsahu v bytech"""
        return sum(content.size_bytes for content in self.offline_content.values())

    def is_available_offline(self, video_id: str) -> bool:
        """Zkontroluje, zda je obsah dostupný offline"""
        content = self.get_offline_content(video_id)
        if not content:
            return False
            
        # Kontrola existence souboru
        return Path(content.file_path).exists() 