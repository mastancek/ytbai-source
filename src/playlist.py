from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import csv
from datetime import datetime
from dataclasses import dataclass, asdict
import logging
from .exceptions import ValidationError

@dataclass
class PlaylistItem:
    """Položka playlistu"""
    title: str
    artist: str
    video_id: str
    duration: str
    added_at: str = None
    
    def __post_init__(self):
        if self.added_at is None:
            self.added_at = datetime.now().isoformat()

@dataclass
class Playlist:
    """Reprezentace playlistu"""
    name: str
    description: str
    items: List[PlaylistItem]
    created_at: str = None
    modified_at: str = None
    
    def __post_init__(self):
        now = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.modified_at is None:
            self.modified_at = now

class PlaylistManager:
    """Správce playlistů"""
    def __init__(self, playlists_dir: Path):
        self.playlists_dir = playlists_dir
        self.playlists_dir.mkdir(parents=True, exist_ok=True)

    def create_playlist(self, name: str, description: str = "") -> Playlist:
        """Vytvoří nový playlist"""
        playlist = Playlist(name=name, description=description, items=[])
        self._save_playlist(playlist)
        return playlist

    def add_to_playlist(self, playlist_name: str, items: List[PlaylistItem]) -> None:
        """Přidá položky do playlistu"""
        playlist = self.load_playlist(playlist_name)
        if playlist:
            playlist.items.extend(items)
            playlist.modified_at = datetime.now().isoformat()
            self._save_playlist(playlist)

    def remove_from_playlist(self, playlist_name: str, video_ids: List[str]) -> None:
        """Odebere položky z playlistu"""
        playlist = self.load_playlist(playlist_name)
        if playlist:
            playlist.items = [
                item for item in playlist.items 
                if item.video_id not in video_ids
            ]
            playlist.modified_at = datetime.now().isoformat()
            self._save_playlist(playlist)

    def load_playlist(self, name: str) -> Optional[Playlist]:
        """Načte playlist ze souboru"""
        try:
            playlist_file = self.playlists_dir / f"{name}.json"
            if not playlist_file.exists():
                return None
                
            with open(playlist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = [PlaylistItem(**item) for item in data['items']]
                return Playlist(
                    name=data['name'],
                    description=data['description'],
                    items=items,
                    created_at=data['created_at'],
                    modified_at=data['modified_at']
                )
        except Exception as e:
            logging.error(f"Chyba při načítání playlistu: {e}")
            return None

    def _save_playlist(self, playlist: Playlist) -> None:
        """Uloží playlist do souboru"""
        try:
            playlist_file = self.playlists_dir / f"{playlist.name}.json"
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(playlist), f, indent=2)
        except Exception as e:
            logging.error(f"Chyba při ukládání playlistu: {e}")
            raise

    def export_playlist(self, name: str, format: str = 'json') -> Path:
        """Exportuje playlist do souboru"""
        playlist = self.load_playlist(name)
        if not playlist:
            raise ValidationError(f"Playlist {name} neexistuje")
            
        export_dir = self.playlists_dir / "exports"
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            export_file = export_dir / f"{name}_{timestamp}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(playlist), f, indent=2)
                
        elif format == 'csv':
            export_file = export_dir / f"{name}_{timestamp}.csv"
            with open(export_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['title', 'artist', 'video_id', 'duration', 'added_at'])
                for item in playlist.items:
                    writer.writerow([
                        item.title, item.artist, item.video_id,
                        item.duration, item.added_at
                    ])
                    
        else:
            raise ValueError(f"Nepodporovaný formát: {format}")
            
        return export_file

    def import_playlist(self, file_path: Path) -> Playlist:
        """Importuje playlist ze souboru"""
        if not file_path.exists():
            raise FileNotFoundError(f"Soubor {file_path} neexistuje")
            
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = [PlaylistItem(**item) for item in data['items']]
                    playlist = Playlist(
                        name=data['name'],
                        description=data['description'],
                        items=items,
                        created_at=data['created_at'],
                        modified_at=datetime.now().isoformat()
                    )
                    
            elif file_path.suffix == '.csv':
                items = []
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        items.append(PlaylistItem(**row))
                        
                playlist = Playlist(
                    name=file_path.stem,
                    description=f"Importováno z {file_path.name}",
                    items=items
                )
                
            else:
                raise ValueError(f"Nepodporovaný formát souboru: {file_path.suffix}")
                
            self._save_playlist(playlist)
            return playlist
            
        except Exception as e:
            logging.error(f"Chyba při importu playlistu: {e}")
            raise 