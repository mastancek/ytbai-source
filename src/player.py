from pathlib import Path
import vlc
import random
import logging
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PlayHistory:
    """Záznam o přehrání skladby"""
    file_path: Path
    played_at: datetime
    duration: int = 0

class MusicPlayer:
    """Třída pro přehrávání hudby"""
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_media = None
        self.playlist: List[Path] = []
        self.current_index = 0
        self.shuffle = False
        self.repeat = False
        self.history: List[PlayHistory] = []

    def play_file(self, file_path: Path) -> None:
        """Přehraje audio soubor"""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Soubor {file_path} neexistuje")

            media = self.instance.media_new(str(file_path))
            self.player.set_media(media)
            self.current_media = media
            self.player.play()
            
            # Přidáme do historie
            self.history.append(PlayHistory(
                file_path=file_path,
                played_at=datetime.now()
            ))
            
        except Exception as e:
            logging.error(f"Chyba při přehrávání: {e}")

    def stop(self) -> None:
        """Zastaví přehrávání"""
        self.player.stop()

    def pause(self) -> None:
        """Pozastaví/obnoví přehrávání"""
        self.player.pause()

    def next_track(self) -> None:
        """Přejde na další skladbu"""
        if not self.playlist:
            return

        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)

        self.play_file(self.playlist[self.current_index])

    def previous_track(self) -> None:
        """Přejde na předchozí skladbu"""
        if not self.playlist:
            return

        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)

        self.play_file(self.playlist[self.current_index])

    def set_playlist(self, files: List[Path]) -> None:
        """Nastaví playlist"""
        self.playlist = files
        self.current_index = 0

    def play_random(self) -> None:
        """Přehraje náhodnou skladbu z playlistu"""
        if not self.playlist:
            return
            
        self.current_index = random.randint(0, len(self.playlist) - 1)
        self.play_file(self.playlist[self.current_index])

    def get_current_time(self) -> int:
        """Vrátí aktuální pozici v sekundách"""
        return self.player.get_time() // 1000

    def get_duration(self) -> int:
        """Vrátí délku aktuální skladby v sekundách"""
        return self.player.get_length() // 1000

    def set_position(self, position: float) -> None:
        """Nastaví pozici přehrávání (0.0 - 1.0)"""
        self.player.set_position(position)

    def get_volume(self) -> int:
        """Vrátí hlasitost (0-100)"""
        return self.player.audio_get_volume()

    def set_volume(self, volume: int) -> None:
        """Nastaví hlasitost (0-100)"""
        self.player.audio_set_volume(volume)

    def is_playing(self) -> bool:
        """Vrátí True pokud se přehrává"""
        return bool(self.player.is_playing())

    def get_history(self, limit: int = 10) -> List[PlayHistory]:
        """Vrátí historii přehrávání"""
        return sorted(
            self.history,
            key=lambda x: x.played_at,
            reverse=True
        )[:limit] 