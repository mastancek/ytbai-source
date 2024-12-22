import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from typing import Dict, Any, List
from pathlib import Path
import pygame
import random
from ..themes.icons import Icons

class MusicPlayer:
    def __init__(self, console: Console, config: Dict[str, Any]):
        self.console = console
        self.config = config
        self.current_song = None
        self.playing = False
        pygame.mixer.init()

    def show_player_menu(self):
        """Menu přehrávače"""
        while True:
            self._show_now_playing()
            self.console.print("\n[cyan]Přehrávač hudby:[/cyan]")
            self.console.print("1. Přehrát skladbu")
            self.console.print("2. Přehrát složku")
            self.console.print("3. Náhodné přehrávání")
            self.console.print("4. Ovládání přehrávání")
            self.console.print("Z. Zpět")

            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                self._stop_playback()
                break
            elif choice == "1":
                self._play_song()
            elif choice == "2":
                self._play_folder()
            elif choice == "3":
                self._random_play()
            elif choice == "4":
                self._playback_controls()

    def _show_now_playing(self):
        """Zobrazí aktuálně přehrávanou skladbu"""
        if self.current_song and self.playing:
            self.console.print(f"\n[green]▶ Přehrává se: {self.current_song}[/green]")
        elif self.current_song:
            self.console.print(f"\n[yellow]⏸ Pozastaveno: {self.current_song}[/yellow]")

    def _play_song(self):
        """Přehraje vybranou skladbu"""
        music_dir = Path(self.config['paths']['music_dir'])
        songs = list(music_dir.glob('**/*.mp3'))
        
        if not songs:
            self.console.print("[yellow]Nenalezeny žádné skladby[/yellow]")
            return

        # Zobrazení seznamu skladeb
        table = Table(title="Dostupné skladby")
        table.add_column("č.", justify="right")
        table.add_column("Skladba")
        
        for i, song in enumerate(songs, 1):
            table.add_row(str(i), song.stem)
        
        self.console.print(table)
        
        choice = Prompt.ask("Vyberte číslo skladby")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(songs):
                self._start_playback(songs[idx])
        except ValueError:
            self.console.print("[red]Neplatná volba[/red]")

    def _play_folder(self):
        """Přehraje všechny skladby ve složce"""
        # TODO: Implementovat přehrávání složky

    def _random_play(self):
        """Náhodné přehrávání"""
        # TODO: Implementovat náhodné přehrávání

    def _playback_controls(self):
        """Ovládání přehrávání"""
        while True:
            self.console.print("\n[cyan]Ovládání:[/cyan]")
            self.console.print("1. Play/Pause")
            self.console.print("2. Stop")
            self.console.print("3. Další")
            self.console.print("4. Předchozí")
            self.console.print("5. Hlasitost +")
            self.console.print("6. Hlasitost -")
            self.console.print("Z. Zpět")

            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice == "1":
                self._toggle_playback()
            elif choice == "2":
                self._stop_playback()
            # TODO: Implementovat další ovládací prvky

    def _start_playback(self, song_path: Path):
        """Spustí přehrávání skladby"""
        try:
            pygame.mixer.music.load(str(song_path))
            pygame.mixer.music.play()
            self.current_song = song_path.stem
            self.playing = True
        except Exception as e:
            self.console.print(f"[red]Chyba při přehrávání: {e}[/red]")

    def _toggle_playback(self):
        """Přepne play/pause"""
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
        else:
            pygame.mixer.music.unpause()
            self.playing = True

    def _stop_playback(self):
        """Zastaví přehrávání"""
        pygame.mixer.music.stop()
        self.playing = False
        self.current_song = None