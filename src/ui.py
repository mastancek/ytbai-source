from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.columns import Columns
from rich.live import Live
from rich.layout import Layout
from rich import box
from typing import List, Set, Dict, Any, Optional, Union, Callable, TypeVar, Generic
from pathlib import Path
from manager import YTBAIManager, SearchResult
from utils import download_and_process_thumbnail, cleanup_thumbnail_cache, get_image_preview
import os
from rich.text import Text
from rich.status import Status
import json
from config import load_config
from themes import ThemeManager
from exceptions import ConfigError, APIError
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from icons import Icons
from icon_sets import IconSets
from player import MusicPlayer
import logging
from tkinter import filedialog
import tkinter as tk
import shutil
import subprocess
import requests
import random
from datetime import datetime
import time
import re
import yt_dlp
from webshare import WebshareDownloader
from themes.default_themes import DefaultThemes
from themes.icon_themes import IconThemes
from themes.icons import Icons
from ai.chat import AIChat
from player.playlist_manager import PlaylistManager
from themes.theme_manager import ThemeManager
from settings.settings_manager import SettingsManager
from ui.core import UICore
from utils.error_handler import ErrorHandler

# Přidání lepšího logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.ytbai' / 'logs' / 'ytbai.log'),
        logging.StreamHandler()
    ]
)

# Přidat typové anotace pro lepší kontrolu typů
T = TypeVar('T')

class UI:
    def __init__(self, manager: YTBAIManager, console: Console):
        self.manager = manager
        self.console = console
        self.config = self._load_config()
        
        # Inicializace modulů
        self.ai_chat = AIChat(manager, console, self.config)
        self.playlist_manager = PlaylistManager(console, self.config)
        self.theme_manager = ThemeManager(console, self.config)
        self.settings_manager = SettingsManager(console, self.config)
        self.ui_core = UICore(console, self.config)
        self.error_handler = ErrorHandler(console)
        
    def start(self):
        """Hlavní smyčka"""
        while True:
            choice = self.ui_core.show_main_menu()
            # Zpracování volby pomocí jednotlivých modulů

    def _load_config(self) -> Dict[str, Any]:
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Validace konfigurace
                    if not isinstance(config, dict):
                        raise ValueError("Neplatný formát konfigurace")
                    return config
            return self._create_default_config()
        except Exception as e:
            logging.error(f"Chyba při načítání konfigurace: {e}")
            return self._create_default_config()

    def save_config(self) -> None:
        """Uloží konfiguraci"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.console.print(f"[error]Chyba při ukládání konfigurace: {e}[/error]")

    def show_main_menu(self) -> str:
        """Zobrazí hlavní menu"""
        options = [
            f"[green]{Icons.get('SEARCH', not self.use_emoji)} 1.[/green] YouTube vyhledávání",
            f"[blue]{Icons.get('AI', not self.use_emoji)} 2.[/blue] AI doporučení hudby",
            f"[cyan]{Icons.get('BRAIN', not self.use_emoji)} 3.[/cyan] YouTube AI mixy",
            f"[yellow]{Icons.get('CHAT', not self.use_emoji)} 4.[/yellow] Chat s hudebním AI",
            f"[magenta]{Icons.get('SETTINGS', not self.use_emoji)} 5.[/magenta] Správa AI služeb",
            f"[green]{Icons.get('THEME', not self.use_emoji)} 6.[/green] Správa nastavení",
            f"[blue]{Icons.get('MUSIC', not self.use_emoji)} 7.[/blue] Přehrávač hudby",
            f"[cyan]{Icons.get('DOWNLOAD', not self.use_emoji)} 8.[/cyan] Webshare stahování",
            f"[red]{Icons.get('EXIT', not self.use_emoji)} K.[/red] Konec"
        ]
        
        self.console.print(Panel(
            "\n".join(options),
            title=f"{Icons.get('MUSIC', not self.use_emoji)} Hlavní Menu",
            border_style="blue"
        ))
        return Prompt.ask("Vyberte možnost").upper()

    def display_results(self, results: List[SearchResult], downloaded_ids: Set[str], selected_indices: Set[int]) -> None:
        """Zobrazí výsledky vyhledávání"""
        table = Table(show_header=True)
        table.add_column("č.", justify="right", style="cyan", width=4)
        table.add_column("Název", style="white", ratio=2)
        table.add_column("Interpret", style="green", ratio=1)
        table.add_column("Délka", style="yellow", width=8)
        table.add_column("Velikost", style="blue", width=10)
        table.add_column("Status", justify="center", width=6)

        for i, result in enumerate(results, 1):
            # Ošetření dlouhých názvů
            title = result.title[:70] + "..." if len(result.title) > 70 else result.title
            artist = result.artist[:30] + "..." if len(result.artist) > 30 else result.artist
            
            # Získání velikosti souboru
            size = self._format_size(getattr(result, 'size', None))
            
            # Status
            status = "[cyan]□[/cyan]"
            if i-1 in selected_indices:
                status = "[cyan]■[/cyan]"
            if result.video_id in downloaded_ids:
                status += " [green]✓[/green]"
            
            table.add_row(
                str(i),
                title,
                artist,
                result.duration,
                size,
                status
            )

        self.console.print(table)

    def discovery_loop(self, initial_results: List[SearchResult]) -> None:
        """Smyčka pro objevování hudby"""
        current_results = initial_results
        downloaded_ids: Set[str] = set()
        selected_indices: Set[int] = set()  # Pro ukládání vybraných skladeb

        if not current_results:
            self.console.print("[yellow]Žádné výsledky k zobrazení[/yellow]")
            return

        while True:
            self.console.clear()
            self.display_results(current_results, downloaded_ids, selected_indices)  # Přidáme selected_indices
            
            options = [
                "[cyan]1-{0}[/cyan] Vybrat/zrušit výběr skladby".format(len(current_results)),
                "[green]S[/green] Stáhnout vybrané skladby",
                "[yellow]N[/yellow] Nové vyhledávání",
                "[yellow]P[/yellow] Podobné skladby",
                "[yellow]V[/yellow] Vybrat vše",
                "[yellow]O[/yellow] Odznačit vše",
                "[red]Z[/red] Zpět"
            ]
            self.console.print("\n".join(options))
            
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "N":
                query = Prompt.ask("Zadejte nový vyhledávací dotaz")
                current_results = self.manager.search_music(query)
                selected_indices.clear()
            elif choice == "P":
                current_results = self.manager.get_recommendations(current_results)
                selected_indices.clear()
            elif choice == "S":
                if not selected_indices:
                    self.console.print("[yellow]Nejsou vybrány žádné skladby[/yellow]")
                    continue
                    
                # Stažení vybraných skladeb
                selected_tracks = [current_results[i] for i in selected_indices]
                with Status(f"[yellow]Stahuji {len(selected_tracks)} skladeb...[/yellow]", spinner="dots"):
                    self.manager.process_download(selected_tracks)
                downloaded_ids.update(track.video_id for track in selected_tracks)
                selected_indices.clear()
                self.console.print(f"[green]Úspěšně staženo {len(selected_tracks)} skladeb[/green]")
            elif choice == "V":
                selected_indices = set(range(len(current_results)))
            elif choice == "O":
                selected_indices.clear()
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(current_results):
                        # Přepínání výběru
                        if index in selected_indices:
                            selected_indices.remove(index)
                        else:
                            selected_indices.add(index)
                    else:
                        self.console.print("[red]Neplatné číslo skladby[/red]")
                except ValueError:
                    self.console.print("[red]Neplatná volba[/red]")

    def _cleanup_all_cache(self) -> None:
        """Vyčistí všechny cache soubory"""
        try:
            # Vyčištění cache náhledů
            if self.cache_dir.exists():
                for file in self.cache_dir.glob('*.jpg'):
                    try:
                        file.unlink()
                    except Exception as e:
                        logging.error(f"Chyba při mazání souboru {file}: {e}")
                
                # Pokus o smazání prázdné složky
                try:
                    self.cache_dir.rmdir()
                except:
                    pass  # Ignorujeme, pokud složka nejde smazat (není prázdná)
            
            self.console.print("[dim]Cache byla vyčištěna[/dim]")
        except Exception as e:
            self.console.print(f"[warning]Chyba při čištění cache: {e}[/warning]")

    def _show_ai_menu(self) -> None:
        """Menu pro AI doporučení hudby"""
        while True:
            # Zjistíme stav jednotlivých služeb
            services = {
                "openai": bool(os.getenv('OPENAI_API_KEY')),
                "ollama": self.manager._check_ollama_server(),  # Kontrola serveru
                "cohere": bool(os.getenv('COHERE_API_KEY')),
                "perplexity": bool(os.getenv('PERPLEXITY_API_KEY')),
                "replicate": bool(os.getenv('REPLICATE_API_TOKEN')),
                "huggingface": bool(os.getenv('HUGGINGFACE_API_KEY'))
            }
            
            # Emoji pro stav služby
            status_emoji = {
                True: "✓",   # Zelená fajfka pro aktivní
                False: "✗"    # Červený křížek pro neaktivní
            }
            
            # Přidáme informace o stavu Ollama
            if services["ollama"]:
                ollama_info = "[green]✓ Server běží[/green]"
            else:
                ollama_info = """[red]✗ Server není dostupný[/red]
                
Pro použití Ollama:
1. Nainstalujte Ollama z [link]https://ollama.ai[/link]
2. Spusťte příkaz: [green]ollama serve[/green]
3. Stáhněte model: [green]ollama pull llama2[/green]"""
            
            options = [
                f"[green]1.[/green] OpenAI GPT {status_emoji[services['openai']]}",
                f"[green]2.[/green] Ollama {status_emoji[services['ollama']]}",
                f"[green]3.[/green] Cohere Command {status_emoji[services['cohere']]}",
                f"[green]4.[/green] Perplexity AI {status_emoji[services['perplexity']]}",
                f"[green]5.[/green] Replicate (Llama 2) {status_emoji[services['replicate']]}",
                f"[green]6.[/green] Hugging Face {status_emoji[services['huggingface']]}",
                "[red]Z.[/red] Zpět"
            ]
            
            # Přidáme informaci o dostupnosti
            available_count = sum(1 for s in services.values() if s)
            status_line = (
                "[green]✓[/green]" if available_count > 0 else "[red]✗[/red]"
                f" Dostupné služby: {available_count}/{len(services)}"
            )
            
            # P��idáme Ollama info pokud je vybraná
            if services["ollama"]:
                status_line += "\n" + ollama_info
            
            self.console.print(Panel(
                "\n".join([status_line, ""] + options),
                title="AI Doporučení Hudby"
            ))
            
            choice = Prompt.ask("Vyberte službu").upper()
            
            if choice == "Z":
                break
            
            # Mapování voleb na služby
            service_map = {
                "1": ("openai", self.manager._get_openai_recommendations),
                "2": ("ollama", self.manager._get_ollama_recommendations),
                "3": ("cohere", self.manager._get_cohere_recommendations),
                "4": ("perplexity", self.manager._get_perplexity_recommendations),
                "5": ("replicate", self.manager._get_replicate_recommendations),
                "6": ("huggingface", self.manager._get_huggingface_recommendations)
            }
            
            if choice in service_map:
                service_name, service_func = service_map[choice]
                if not services[service_name]:
                    self.console.print(f"[red]Služba {service_name} není nakonfigurována![/red]")
                    continue
                    
                mood = Prompt.ask("Zadejte náladu nebo styl hudby")
                try:
                    with Status(f"[yellow]Získávám doporučen od {service_name}...[/yellow]", spinner="dots"):
                        results = service_func(mood)
                    if results:
                        self.discovery_loop(results)
                    else:
                        self.console.print("[yellow]Žádná doporučení nebyla nalezena[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]Chyba: {str(e)}[/red]")
            
            elif choice == "7":
                self._ai_chat()
            elif choice == "2":  # Ollama
                try:
                    if not self.manager._check_ollama_server():
                        self.console.print("""
[red]Ollama server není dostupný![/red]

Pro použití Ollama:
1. Nainstalujte Ollama z [link]https://ollama.ai[/link]
2. Spus���te příkaz: [green]ollama serve[/green]
3. Stáhněte model: [green]ollama pull llama2[/green]

[yellow]Tip: Nechte příkaz 'ollama serve' běžet v samostatném terminálu[/yellow]
                        """)
                        continue
                    
                    mood = Prompt.ask("Zadejte náladu nebo styl hudby")
                    with Status("[yellow]Získávám doporučení od Ollama...[/yellow]", spinner="dots"):
                        results = self.manager._get_ollama_recommendations(mood)
                    if results:
                        self.discovery_loop(results)
                    else:
                        self.console.print("[yellow]Žádná doporučení nebyla nalezena[/yellow]")
                except ConfigError as e:
                    self.console.print(str(e))
                except Exception as e:
                    self.console.print(f"[red]Neočekávaná chyba: {str(e)}[/red]")

    def _youtube_ai_menu(self) -> None:
        """Menu pro YouTube AI doporučení"""
        while True:
            options = [
                "[green]1.[/green] Najít podobné skladby",
                "[green]2.[/green] Mix podle nálady",
                "[green]3.[/green] Mix podle žánru",
                "[green]4.[/green] Playlist podle interpreta",
                "[green]5.[/green] Trending mixy",
                "[red]Z.[/red] Zpět"
            ]
            
            self.console.print(Panel("\n".join(options), title="YouTube AI"))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                query = Prompt.ask("Zadejte název skladby nebo interpreta pro hledání podobnch")
                results = self.manager.search_music(f"{query} similar songs mix", use_youtube_ai=True)
                if results:
                    self.discovery_loop(results)
            elif choice == "2":
                mood = Prompt.ask("Zadejte náladu (např. relaxing, workout, party, focus)")
                results = self.manager.search_music(f"best {mood} music mix playlist", use_youtube_ai=True)
                if results:
                    self.discovery_loop(results)
            elif choice == "3":
                genre = Prompt.ask("Zadejte žánr (např. rock, jazz, electronic)")
                results = self.manager.search_music(f"best {genre} mix compilation", use_youtube_ai=True)
                if results:
                    self.discovery_loop(results)
            elif choice == "4":
                artist = Prompt.ask("Zadejte jméno interpreta")
                results = self.manager.search_music(f"{artist} greatest hits mix playlist", use_youtube_ai=True)
                if results:
                    self.discovery_loop(results)
            elif choice == "5":
                options = [
                    "Popular Music Mix 2024",
                    "Top Hits Mix",
                    "Viral Songs Playlist",
                    "New Music This Week",
                    "Trending Music Mix"
                ]
                self.console.print("[yellow]Vyberte typ trending mixu:[/yellow]")
                for i, opt in enumerate(options, 1):
                    self.console.print(f"[dim]{i}. {opt}[/dim]")
                
                try:
                    idx = int(Prompt.ask("Vaše volba")) - 1
                    if 0 <= idx < len(options):
                        results = self.manager.search_music(options[idx], use_youtube_ai=True)
                        if results:
                            self.discovery_loop(results)
                    else:
                        self.console.print("[red]Neplatná volba[/red]")
                except ValueError:
                    self.console.print("[red]Neplatná volba[/red]")

    def _chatgpt_ai_menu(self) -> None:
        """Menu pro ChatGPT hudebního asistenta"""
        while True:
            options = [
                "[green]1.[/green] Doporučení podle nálady",
                "[green]2.[/green] Doporučení podle žánru",
                "[green]3.[/green] Doporučení podle aktivity",
                "[red]Z.[/red] Zpět"
            ]
            
            self.console.print(Panel("\n".join(options), title="AI Asistent"))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                mood = Prompt.ask("Zadejte náladu (např. happy, sad, energetic)")
                results = self.manager.get_ai_recommendations(mood)
                if results:
                    self.discovery_loop(results)
            elif choice == "2":
                genre = Prompt.ask("Zadejte žánr (např. rock, jazz, electronic)")
                results = self.manager.get_ai_recommendations(f"best {genre} songs")
                if results:
                    self.discovery_loop(results)
            elif choice == "3":
                activity = Prompt.ask("Zadejte aktivitu (např. workout, study, relax)")
                results = self.manager.get_ai_recommendations(f"music for {activity}")
                if results:
                    self.discovery_loop(results)

    def _show_settings_menu(self) -> None:
        """Menu pro správu nastavení"""
        theme = self.theme_manager.get_theme()
        while True:
            options = [
                f"[{theme.get('primary')}]1.[/] Správa API klíčů",
                f"[{theme.get('secondary')}]2.[/] Správa AI modelů",
                f"[{theme.get('accent')}]3.[/] Nastavení stahování",
                f"[{theme.get('info')}]4.[/] Nastavení složek",
                f"[{theme.get('success')}]5.[/] Správa témat",
                f"[{theme.get('warning')}]6.[/] Správa ikon",
                f"[{theme.get('muted')}]7.[/] Zobrazit aktuální nastavení",
                f"[{theme.get('error')}]8.[/] Zpět"
            ]
            
            self.console.print(Panel(
                "\n".join(options),
                title="Nastavení",
                border_style=theme.get('primary'),
                title_align="center",
                padding=(1, 2)
            ))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "8":
                break
            elif choice == "1":
                self._manage_api_keys()
            elif choice == "2":
                self._manage_ai_models()
            elif choice == "3":
                self._manage_download_settings()
            elif choice == "4":
                self._manage_folders()
            elif choice == "5":
                self._manage_themes()
            elif choice == "6":
                self._manage_icons()
            elif choice == "7":
                self._show_current_settings()

    def _manage_api_keys(self) -> None:
        """Správa API klíčů"""
        while True:
            options = [
                "[green]1.[/green] Přidat/upravit OpenAI API klíč",
                "[green]2.[/green] Přidat/upravit Perplexity API klíč",
                "[green]3.[/green] Přidat/upravit Cohere API klíč",
                "[green]4.[/green] Přidat/upravit Replicate API token",
                "[green]5.[/green] Přidat/upravit Hugging Face API klíč",
                "[green]6.[/green] Zobrazit nastavené API klíče",
                "[green]7.[/green] Zpět"
            ]
            
            self.console.print(Panel("\n".join(options), title="Správa API Klíčů"))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "7":
                break
            elif choice in ["1", "2", "3", "4", "5"]:
                api_names = {
                    "1": "OPENAI_API_KEY",
                    "2": "PERPLEXITY_API_KEY",
                    "3": "COHERE_API_KEY",
                    "4": "REPLICATE_API_TOKEN",
                    "5": "HUGGINGFACE_API_KEY"
                }
                key = Prompt.ask("Zadejte API klíč", password=True)
                self._update_env_file(api_names[choice], key)
                self.console.print("[green]API klíč byl aktualizován[/green]")
            elif choice == "6":
                self._show_api_keys()

    def _manage_download_settings(self) -> None:
        """Správa nastavení stahování"""
        while True:
            current_settings = self.config.get('download', {})
            cover_settings = current_settings.get('cover_art', {
                'enabled': True,
                'size': 500,
                'format': 'jpg',
                'quality': 85
            })
            
            options = [
                f"[green]1.[/green] Změnit kvalitu MP3 (současná: {current_settings.get('quality', '192k')})",
                f"[green]2.[/green] Změnit formát (současný: {current_settings.get('format', 'mp3')})",
                f"[green]3.[/green] Nastavení cover art (velikost: {cover_settings['size']}x{cover_settings['size']})",
                f"[green]4.[/green] Nastavení normalizace zvuku",
                "[red]Z.[/red] Zpět"
            ]
            
            self.console.print(Panel("\n".join(options), title="Nastavení Stahování"))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "3":
                self._manage_cover_art_settings()

    def _manage_cover_art_settings(self) -> None:
        """Nastavení cover art"""
        while True:
            current_settings = self.config.get('download', {}).get('cover_art', {
                'enabled': True,
                'size': 500,
                'format': 'jpg',
                'quality': 85
            })  # Opraveno - byla zde přebytečná závorka
            
            # Přednastavené velikosti
            preset_sizes = {
                "1": "300x300",
                "2": "400x400",
                "3": "500x500",
                "4": "600x600",
                "5": "800x800",
                "6": "1000x1000"
            }
            
            options = [
                f"[green]1.[/green] Zapnout/vypnout cover art (současný stav: {'zapnuto' if current_settings['enabled'] else 'vypnuto'})",
                f"[green]2.[/green] Změnit velikost (současná: {current_settings['size']}x{current_settings['size']})",
                f"[green]3.[/green] Změnit formát (současný: {current_settings['format']})",
                f"[green]4.[/green] Změnit kvalitu JPEG (současná: {current_settings['quality']})",
                "[red]Z.[/red] Zpět"
            ]
            
            info = [
                "",
                "[bold]Doporučená nastavení:[/bold]",
                "- Velikost: 500x500 px (standardní velikost)",
                "- Formát: JPG (menší velikost souboru)",
                "- Kvalita JPEG: 85 (dobrý poměr kvalita/velikost)",
                "",
                "[bold]Dostupné velikosti:[/bold]",
                "1. 300x300 px (malá velikost)",
                "2. 400x400 px",
                "3. 500x500 px (doporučeno)",
                "4. 600x600 px",
                "5. 800x800 px",
                "6. 1000x1000 px (velká velikost)",
                "",
                "[dim]Cover art se automaticky stáhne z YouTube a upraví podle nastavení[/dim]"
            ]
            
            self.console.print(Panel("\n".join(options + info), title="Nastavení Cover Art"))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                enabled = Prompt.ask("Zapnout cover art? [y/n]", choices=['y', 'n']) == 'y'
                self.config.setdefault('download', {}).setdefault('cover_art', {})['enabled'] = enabled
            elif choice == "2":
                size_choice = Prompt.ask(
                    "Vyberte velikost (1-6) nebo zadejte vlastní (např. 450x450)",
                    default="3"
                )
                
                try:
                    if size_choice in preset_sizes:
                        # Použijeme přednastavenou velikost
                        size = int(preset_sizes[size_choice].split('x')[0])
                    else:
                        # Parsování vlastní velikosti
                        if 'x' in size_choice:
                            width = int(size_choice.split('x')[0])
                            if 300 <= width <= 1000:
                                size = width
                            else:
                                raise ValueError("Velikost musí být mezi 300 a 1000 px")
                        else:
                            raise ValueError("Neplatný formát")
                    
                    self.config.setdefault('download', {}).setdefault('cover_art', {})['size'] = size
                    self.console.print(f"[success]Nastavena velikost {size}x{size} px[/success]")
                    
                except ValueError as e:
                    self.console.print(f"[red]Neplatná velikost: {e}[/red]")
                
            elif choice == "3":
                format = Prompt.ask("Vyberte formát", choices=['jpg', 'png'])
                self.config.setdefault('download', {}).setdefault('cover_art', {})['format'] = format
            elif choice == "4":
                while True:
                    quality = Prompt.ask("Zadejte kvalitu JPEG (0-100)")
                    try:
                        quality = int(quality)
                        if 0 <= quality <= 100:
                            self.config.setdefault('download', {}).setdefault('cover_art', {})['quality'] = quality
                            break
                        else:
                            self.console.print("[red]Kvalita musí být mezi 0 a 100[/red]")
                    except ValueError:
                        self.console.print("[red]Neplatná hodnota[/red]")
            
            self.save_config()

    def _manage_folders(self) -> None:
        """Správa složek pro stahování"""
        while True:
            current_paths = self.config.get('paths', {
                'music_dir': str(Path.home() / "Music" / "YouTube"),
                'cache_dir': str(Path.home() / ".ytbai" / "cache"),
                'logs_dir': str(Path.home() / ".ytbai" / "logs")
            })

            options = [
                f"[green]1.[/green] Změnit složku pro stahování (současná: {current_paths['music_dir']})",
                f"[green]2.[/green] Změnit složku pro cache (současná: {current_paths['cache_dir']})",
                f"[green]3.[/green] Změnit složku pro logy (současná: {current_paths['logs_dir']})",
                "[red]Z.[/red] Zpět"
            ]
            
            # Zobrazení menu
            self.console.print(Panel("\n".join(options), title="Správa Složek"))  # Opraveno - odstraněna přebývající závorka
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice in ["1", "2", "3"]:
                # Vytvoříme skryté Tk okno
                root = tk.Tk()
                root.withdraw()  # Skryjeme hlavní okno
                
                # Dostaneme okno do popředí
                root.lift()
                root.attributes('-topmost', True)
                
                # Na Windows navíc
                if os.name == 'nt':
                    root.focus_force()
                
                # Vchozí cesta podle volby
                path_key = {
                    "1": "music_dir",
                    "2": "cache_dir",
                    "3": "logs_dir"
                }[choice]
                initial_dir = current_paths[path_key]
                
                # Otevřeme dialog pro výběr složky
                new_path = filedialog.askdirectory(
                    title="Vyberte složku",
                    initialdir=initial_dir,
                    parent=root  # Nastavíme rodiče dialogu
                )
                
                # Zrušíme Tk okno
                root.destroy()
                
                if new_path:  # Pokud uživatel nevybral Cancel
                    try:
                        # Převedeme na Path objekt a vytvoříme složku
                        new_path = Path(new_path).resolve()
                        new_path.mkdir(parents=True, exist_ok=True)
                        
                        # Uložíme do konfigurace
                        self.config.setdefault('paths', {})[path_key] = str(new_path)
                        self.save_config()
                        self.console.print(f"[success]Složka byla změněna na: {new_path}[/success]")
                    except Exception as e:
                        self.console.print(f"[error]Chyba při změně složky: {e}[/error]")

    def _show_current_settings(self) -> None:
        """Zobrazí aktuální nastavení"""
        table = Table(title="Aktuální Nastavení")
        table.add_column("Nastavení", style="cyan")
        table.add_column("Hodnota", style="green")
        
        # Přidme řádky s nastaveními
        table.add_row("Složka pro stahování", str(Path.home() / "Music" / "YouTube"))
        table.add_row("Kvalita MP3", "192k")
        table.add_row("Formát", "mp3")
        table.add_row("Normalizace zvuku", "Zapnuto")
        
        self.console.print(table)

    def _update_env_file(self, key: str, value: str) -> None:
        """Aktualizuje .env soubor"""
        env_path = self.manager.project_root / ".env"
        
        # Načteme současný obsah
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Najdeme a aktualizujeme klíč
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        # Pokud klíč neexistuje, přidáme ho
        if not key_found:
            lines.append(f"{key}={value}\n")
        
        # Zapíšeme zpět do souboru
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def _manage_ai_services(self) -> None:
        """Menu pro správu AI služeb"""
        while True:
            services = {
                "OpenAI": bool(os.getenv('OPENAI_API_KEY')),
                "Ollama": True,  # Ollama je vždy dostupná lokálně
                "Perplexity": bool(os.getenv('PERPLEXITY_API_KEY')),
                "Cohere": bool(os.getenv('COHERE_API_KEY')),
                "Replicate": bool(os.getenv('REPLICATE_API_TOKEN')),
                "Hugging Face": bool(os.getenv('HUGGINGFACE_API_KEY'))
            }
            
            options = [
                f"[{'green' if services['OpenAI'] else 'red'}]1.[/] OpenAI (GPT-3.5) {'✓' if services['OpenAI'] else '✗'}",
                f"[{'green' if services['Ollama'] else 'red'}]2.[/] Ollama {'✓' if services['Ollama'] else '✗'}",
                f"[{'green' if services['Perplexity'] else 'red'}]3.[/] Perplexity AI {'✓' if services['Perplexity'] else '✗'}",
                f"[{'green' if services['Cohere'] else 'red'}]4.[/] Cohere {'✓' if services['Cohere'] else '✗'}",
                f"[{'green' if services['Replicate'] else 'red'}]5.[/] Replicate (Llama 2) {'✓' if services['Replicate'] else '✗'}",
                f"[{'green' if services['Hugging Face'] else 'red'}]6.[/] Hugging Face {'✓' if services['Hugging Face'] else '✗'}",
                "[yellow]7.[/yellow] Test dostupných služeb",
                "[red]Z.[/red] Zpět"
            ]
            
            self.console.print(Panel("\n".join(options), title="Správa AI Služeb"))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice in ["1", "2", "3", "4", "5", "6"]:
                self._manage_api_keys()  # Přesměrujeme na správu API klíčů
            elif choice == "7":
                self._test_ai_services()  # Test funkčnosti služeb

    def _manage_ai_models(self) -> None:
        """Menu pro správu AI modelů"""
        while True:
            config = load_config(self.manager.project_root / "config")
            ai_config = config.get("ai_services", {})
            
            options = []
            for service, settings in ai_config.items():
                current_model = settings.get("model", "není nastaven")
                options.append(
                    f"[green]{service.capitalize()}[/green]\n"
                    f"  Model: [yellow]{current_model}[/yellow]\n"
                    f"  Max tokenů: {settings.get('max_tokens', 'N/A')}\n"
                    f"  Teplota: {settings.get('temperature', 'N/A')}"
                )
            
            options.append("[red]Z.[/red] Zpět")
            
            self.console.print(Panel("\n".join(options), title="Správa AI Modelů"))
            choice = Prompt.ask("Vyberte službu pro úpravu").lower()
            
            if choice == "z":
                break
            elif choice in ai_config:
                self._edit_model_settings(choice, ai_config[choice])

    def _edit_model_settings(self, service: str, current_settings: dict) -> None:
        """Editor nastavení pro konkrétn AI model"""
        if service == "huggingface" and not self.manager.hf_api:
            self.console.print("[red]Hugging Face API není nakonfigurováno![/red]")
            return

        # Získáme dostupné modely z API
        available_models = self.manager.get_available_models(service)
        
        if not available_models:
            self.console.print("[yellow]Nepodařilo se získat seznam modelů, používám offline seznam[/yellow]")
            # ... zbytek kódu ...

    def _show_api_keys(self) -> None:
        """Zobrazí nastavené API klíče"""
        table = Table(show_header=True)
        table.add_column("Služba", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("API Klíč", style="yellow")
        
        api_keys = {
            "OpenAI": "OPENAI_API_KEY",
            "Perplexity": "PERPLEXITY_API_KEY",
            "Cohere": "COHERE_API_KEY",
            "Replicate": "REPLICATE_API_TOKEN",
            "Hugging Face": "HUGGINGFACE_API_KEY"
        }
        
        for service, env_key in api_keys.items():
            key = os.getenv(env_key, "")
            # Skryjeme většinu znaků API klíče pro bezpečnost
            masked_key = "••••" + key[-4:] if key else ""
            status = "[green]✓[/green]" if key else "[red]✗[/red]"
            
            table.add_row(
                service,
                status,
                masked_key if key else "[red]Nenastaveno[/red]"
            )
        
        self.console.print("\n[bold]Nastavené API klíče:[/bold]")
        self.console.print(table)
        self.console.print("\n[dim]Poznámka: Z bezpečnostních důvodů jsou API klíče částečně skrytý[/dim]")

    def _test_ai_services(self) -> None:
        """Test dostupnosti a funkčnosti AI služeb"""
        table = Table(show_header=True)
        table.add_column("Služba", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Odpověď", style="green", max_width=50)
        
        test_prompt = "Doporuč mi nějakou veselou písničku."
        
        # Test OpenAI
        try:
            if os.getenv('OPENAI_API_KEY'):
                response = self.manager.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=50
                )
                table.add_row(
                    "OpenAI",
                    "[green]✓[/green]",
                    response.choices[0].message.content[:50] + "..."
                )
            else:
                table.add_row("OpenAI", "[red]✗[/red]", "API klíč není nastaven")
        except Exception as e:
            table.add_row("OpenAI", "[red]✗[/red]", str(e)[:50])

        # Test Cohere
        try:
            if os.getenv('COHERE_API_KEY'):
                response = self.manager.co.chat(
                    message=test_prompt,
                    model="command",  # nebo "command-light", "command-nightly", "command-r"
                    temperature=0.7,
                    stream=False,
                    citation_quality="accurate",
                    connectors=[],
                    documents=[]
                )
                table.add_row(
                    "Cohere",
                    "[green]✓[/green]",
                    response.text if hasattr(response, 'text') else response.message[:50] + "..."
                )
            else:
                table.add_row("Cohere", "[red]✗[/red]", "API klíč není nastaven")
        except Exception as e:
            table.add_row("Cohere", "[red]✗[/red]", str(e)[:50])

        # Test Hugging Face
        try:
            if os.getenv('HUGGINGFACE_API_KEY'):
                response = self.manager.text_generator.text_generation(
                    test_prompt,
                    max_new_tokens=50
                )
                table.add_row(
                    "Hugging Face",
                    "[green]✓[/green]",
                    response.generated_text[:50] + "..."
                )
            else:
                table.add_row("Hugging Face", "[red]✗[/red]", "API klíč není nastaven")
        except Exception as e:
            table.add_row("Hugging Face", "[red]✗[/red]", str(e)[:50])

        # Test Replicate
        try:
            if os.getenv('REPLICATE_API_TOKEN'):
                output = self.manager.replicate.run(
                    "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
                    input={"prompt": test_prompt, "max_new_tokens": 50}
                )
                table.add_row(
                    "Replicate",
                    "[green]✓[/green]",
                    str(output)[:50] + "..."
                )
            else:
                table.add_row("Replicate", "[red]✗[/red]", "API klíč není nastaven")
        except Exception as e:
            table.add_row("Replicate", "[red]✗[/red]", str(e)[:50])

        # Test Perplexity
        try:
            if os.getenv('PERPLEXITY_API_KEY'):
                response = self.manager.perplexity.generate(test_prompt)
                table.add_row(
                    "Perplexity",
                    "[green]✓[/green]",
                    response[:50] + "..."
                )
            else:
                table.add_row("Perplexity", "[red]✗[/red]", "API klíč není nastaven")
        except Exception as e:
            table.add_row("Perplexity", "[red]✗[/red]", str(e)[:50])

        # Test Ollama
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama2',
                    'prompt': test_prompt,
                    'stream': False
                }
            )
            table.add_row(
                "Ollama",
                "[green]✓[/green]",
                response.json()['response'][:50] + "..."
            )
        except Exception as e:
            table.add_row("Ollama", "[red]✗[/red]", str(e)[:50])

        self.console.print("\n[bold]Test AI služeb:[/bold]")
        self.console.print(table)
        self.console.print("\n[dim]✓ = Služba je dostupná a funkční[/dim]")
        self.console.print("[dim]✗ = Služba není dostupná nebo nefunguje správně[/dim]")

    def _manage_themes(self) -> None:
        """Menu pro správu témat"""
        while True:
            themes = DefaultThemes.get_all_themes()
            current_theme = self.config.get('theme', 'dracula')
            
            options = [
                f"[green]1.[/green] Změnit téma (aktuální: {current_theme})",
                "[green]2.[/green] Vytvořit vlastní téma",
                "[green]3.[/green] Smazat vlastní téma",
                "[red]Z.[/red] Zpět"
            ]
            
            # Zobrazení menu
            self.console.print(Panel("\n".join(options), title="Správa Témat")) # Odstraněna přebývající závorka
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                # Zobrazení dostupných témat
                table = Table(show_header=True)
                table.add_column("č.", justify="right", style="cyan")
                table.add_column("Název", style="green")
                table.add_column("Popis", style="yellow")
                
                for i, (name, theme) in enumerate(themes.items(), 1):
                    table.add_row(
                        str(i),
                        name,
                        theme.description
                    )
                
                self.console.print(table)
                
                # Výběr tématu
                theme_choice = Prompt.ask("\nVyberte téma (číslo nebo název)")
                try:
                    if theme_choice.isdigit():
                        idx = int(theme_choice) - 1
                        if 0 <= idx < len(themes):
                            theme_name = list(themes.keys())[idx]
                        else:
                            raise ValueError("Neplatné číslo tématu")
                    else:
                        theme_name = theme_choice
                    
                    # Aplikace nového tématu
                    theme = DefaultThemes.get_theme(theme_name)
                    self.console = Console(theme=theme)
                    self.config['theme'] = theme_name
                    self.save_config()
                    
                    self.console.print(f"[success]Téma {theme_name} bylo aktivováno[/success]")
                except Exception as e:
                    self.console.print(f"[error]{str(e)}[/error]")
            
            elif choice == "2":
                name = Prompt.ask("Název nového tématu")
                if name in themes:
                    self.console.print("[error]Téma s tímto názvem již existuje[/error]")
                    continue
                
                # Průvodce vytvořením tématu
                colors = {}
                for field in ["primary", "secondary", "accent", "text"]:
                    color = Prompt.ask(f"Zadejte barvu pro {field}", 
                                     default=self.theme_manager.DEFAULT_THEMES["default"].__dict__[field])
                    colors[field] = color
                
                try:
                    scheme = ColorScheme(**colors)
                    self.theme_manager.create_custom_theme(name, scheme)
                    self.console.print("[success]Téma bylo vytvořeno[/success]")
                except Exception as e:
                    self.console.print(f"[error]Chyba při vytváření tématu: {str(e)}[/error]")
            
            elif choice == "3":
                custom_themes = {
                    name: type_ for name, type_ in themes.items()
                    if type_ == "vlastní"
                }
                
                if not custom_themes:
                    self.console.print("[warning]Nemáte žádná vlastní témata[/warning]")
                    continue
                
                self.console.print("\nVlastní témata:")
                for name in custom_themes:
                    self.console.print(f"- {name}")
                
                name = Prompt.ask("\nZadejte název tématu ke smazání")
                try:
                    self.theme_manager.delete_custom_theme(name)
                    self.console.print("[success]Téma bylo smazáno[/success]")
                except ConfigError as e:
                    self.console.print(f"[error]{str(e)}[/error]")

    def _manage_icons(self) -> None:
        """Menu pro správu ikon"""
        while True:
            icon_sets = IconSets.get_all_sets()
            current_set = self.config.get('icon_set', 'emoji')
            
            options = [
                f"[green]1.[/green] Změnit sadu ikon (aktuální: {current_set})",
                "[red]Z.[/red] Zpět"
            ]
            
            # Zobrazení menu
            self.console.print(Panel("\n".join(options), title="Správa Ikon"))  # Odstranna přebývající závorka
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                # Zobrazení dostupných sad
                table = Table(show_header=True)
                table.add_column("Číslo", style="cyan", justify="right")
                table.add_column("Název", style="green")
                table.add_column("Popis", style="yellow")
                table.add_column("Ukázka", style="white")
                
                for i, (name, icon_set) in enumerate(icon_sets.items(), 1):
                    # Ukázka několika ikon ze sady
                    preview = f"{icon_set.music} {icon_set.play} {icon_set.settings}"
                    table.add_row(
                        str(i),
                        name,
                        icon_set.description,
                        preview
                    )
                
                self.console.print(table)
                
                # Výběr sady
                set_choice = Prompt.ask("\nVyberte sadu ikon (číslo nebo název)")
                try:
                    if set_choice.isdigit():
                        idx = int(set_choice) - 1
                        if 0 <= idx < len(icon_sets):
                            set_name = list(icon_sets.keys())[idx]
                        else:
                            raise ValueError("Neplatné číslo sady")
                    else:
                        set_name = set_choice
                        
                    if set_name not in icon_sets:
                        raise ValueError(f"Sada '{set_name}' neexistuje")
                        
                    # Uložení vybrané sady
                    Icons.set_active_set(set_name)
                    self.config['icon_set'] = set_name
                    self.save_config()
                    self.console.print(f"[success]Sada ikon {set_name} byla aktivována[/success]")
                    
                except Exception as e:
                    self.console.print(f"[error]{str(e)}[/error]")

    def _show_player_menu(self) -> None:
        """Menu pro přehrávač hudby"""
        while True:
            # Zjistíme aktuální stav pehrávače
            now_playing = ""
            if self.player.current_media:
                now_playing = f"\n[bold]Nyní hraje:[/bold] {self.player.current_media.get_meta(0)}"
                if self.player.is_playing():
                    now_playing += " [green]▶[/green]"
                else:
                    now_playing += " [yellow]⏸[/yellow]"

            options = [
                f"[{self.theme['primary']}]{Icons.get('PLAY', not self.use_emoji)} 1.[/] Přehrát skladby",
                f"[{self.theme['secondary']}]{Icons.get('PLAYLIST', not self.use_emoji)} 2.[/] Správa playlistů",
                f"[{self.theme['accent']}]{Icons.get('SHUFFLE', not self.use_emoji)} 3.[/] Náhodné přehrávání",
                f"[{self.theme['info']}]{Icons.get('REPEAT', not self.use_emoji)} 4.[/] Historie přehrávání",
                f"[{self.theme['error']}]{Icons.get('BACK', not self.use_emoji)} Z.[/] Zpět"
            ]

            if self.player.is_playing():
                options.insert(1, f"[{self.theme['warning']}]{Icons.get('PAUSE', not self.use_emoji)} P.[/] Pozastavit")
                options.insert(2, f"[{self.theme['error']}]{Icons.get('STOP', not self.use_emoji)} S.[/] Zastavit")
            
            self.console.print(Panel(
                now_playing + "\n\n" + "\n".join(options),
                title=f"{Icons.get('MUSIC', not self.use_emoji)} Přehrávač",
                border_style=self.theme.get('primary')
            ))
            
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                self._play_music_menu()
            elif choice == "P" and self.player.is_playing():
                self.player.pause()
            elif choice == "S" and self.player.is_playing():
                self.player.stop()
            elif choice == "2":
                self._manage_playlists()
            elif choice == "3":
                self.player.shuffle = True
                self.player.play_random()
            elif choice == "4":
                self._show_play_history()

    def _play_music_menu(self) -> None:
        """Menu pro vběr a pehrávání skladeb"""
        music_dir = Path(self.config['paths']['music_dir'])
        
        # Kontrola existence složky
        if not music_dir.exists():
            self.console.print(f"[yellow]Složka {music_dir} neexistuje![/yellow]")
            if Prompt.ask("Chcete ji vytvořit? [y/n]", choices=['y', 'n']) == 'y':
                music_dir.mkdir(parents=True, exist_ok=True)
                self.console.print("[green]Složka byla vytvořena[/green]")
            return

        # Načtení všech MP3 souborů (včetně podsložek)
        files = list(music_dir.rglob('*.mp3'))
        
        if not files:
            self.console.print("[yellow]Žádné skladby k přehrání[/yellow]")
            self.console.print(f"[dim]Stáhněte nějaké skladby do složky {music_dir}[/dim]")
            return
        
        selected_indices: Set[int] = set()
        
        while True:
            self.console.clear()
            # Zobrazíme seznam skladeb
            table = Table(show_header=True)
            table.add_column("č.", justify="right", style="cyan", width=4)
            table.add_column("Název", style="white")
            table.add_column("Složka", style="blue")
            table.add_column("Délka", style="yellow", width=8)
            table.add_column("Status", justify="center", width=6)
            
            for i, file in enumerate(files, 1):
                # Indiktor výběru a přehrávání
                status = ""
                if i-1 in selected_indices:
                    status += "[cyan]■[/cyan]"
                if self.player.current_media and str(file) == self.player.current_media.get_mrl():
                    status += " [green]▶[/green]"
                
                # Získání relativní cesty pro zobrazení složky
                rel_path = file.relative_to(music_dir).parent
                folder = str(rel_path) if str(rel_path) != "." else ""
                
                table.add_row(
                    str(i),
                    file.stem,
                    folder,
                    self._get_audio_duration(file),
                    status
                )
            
            self.console.print(table)
            
            # Ovládací menu
            options = [
                "[cyan]1-{0}[/cyan] Vybrat/zrušit výběr skladby".format(len(files)),
                "[green]P[/green] Přehrát vybrané skladby",
                "[yellow]V[/yellow] Vybrat vše",
                "[yellow]O[/yellow] Odznačit vše",
                "[red]Z[/red] Zpět"
            ]
            self.console.print("\n".join(options))
            
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "P":
                if not selected_indices:
                    self.console.print("[yellow]Nejsou vybrány žádné skladby[/yellow]")
                    continue
                
                # Vytvoříme playlist z vybraných skladeb
                selected_files = [files[i] for i in selected_indices]
                self.player.set_playlist(selected_files)
                self.player.play_file(selected_files[0])  # Začneme první skladbou
                break
            elif choice == "V":
                selected_indices = set(range(len(files)))
            elif choice == "O":
                selected_indices.clear()
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(files):
                        if index in selected_indices:
                            selected_indices.remove(index)
                        else:
                            selected_indices.add(index)
                    else:
                        self.console.print("[red]Neplatné číslo skladby[/red]")
                except ValueError:
                    self.console.print("[red]Neplatná volba[/red]")

    def _get_audio_duration(self, file_path: Path) -> str:
        """Získá délku audio souboru"""
        try:
            media = self.player.instance.media_new(str(file_path))
            media.parse()
            duration = media.get_duration() // 1000  # převod na sekundy
            return f"{duration // 60}:{duration % 60:02d}"
        except:
            return "--:--"

    def _manage_playlists(self) -> None:
        """Menu pro správu playlistů"""
        while True:
            options = [
                f"[{self.theme['primary']}]1.[/] Vytvořit playlist",
                f"[{self.theme['secondary']}]2.[/] Načíst playlist",
                f"[{self.theme['accent']}]3.[/] Upravit playlist",
                f"[{self.theme['error']}]Z.[/] Zpět"
            ]
            
            self.console.print(Panel(
                "\n".join(options),
                title=f"{Icons.get('PLAYLIST', not self.use_emoji)} Správa playlistů",
                border_style=self.theme.get('primary')
            ))
            
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "1":
                self._create_playlist()
            elif choice == "2":
                self._load_playlist()
            elif choice == "3":
                self._edit_playlist()

    def _create_playlist(self) -> None:
        """Vytvoření nového playlistu"""
        name = Prompt.ask("Název playlistu")
        playlist_dir = self.manager.project_root / "playlists"
        playlist_dir.mkdir(exist_ok=True)
        
        playlist_file = playlist_dir / f"{name}.m3u"
        if playlist_file.exists():
            self.console.print("[yellow]Playlist s tímto názvem již existuje[/yellow]")
            return
        
        # Výběr skladeb
        music_dir = Path(self.config['paths']['music_dir'])
        files = list(music_dir.glob('*.mp3'))
        selected_indices: Set[int] = set()
        
        while True:
            self.console.clear()
            table = Table(show_header=True)
            table.add_column("č.", justify="right", style="cyan", width=4)
            table.add_column("Název", style="white")
            table.add_column("Status", justify="center", width=6)
            
            for i, file in enumerate(files, 1):
                status = "[cyan]■[/cyan]" if i-1 in selected_indices else ""
                table.add_row(str(i), file.stem, status)
            
            self.console.print(table)
            
            options = [
                "[cyan]1-{0}[/cyan] Vybrat/zrušit skladbu".format(len(files)),
                "[green]U[/green] Uložit playlist",
                "[yellow]V[/yellow] Vybrat vše",
                "[yellow]O[/yellow] Odznačit vše",
                "[red]Z[/red] Zpět"
            ]
            self.console.print("\n".join(options))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "U":
                if not selected_indices:
                    self.console.print("[yellow]Nejsou vybrány žádné skladby[/yellow]")
                    continue
                
                # Uložíme playlist
                selected_files = [files[i] for i in selected_indices]
                with open(playlist_file, 'w', encoding='utf-8') as f:
                    f.write("#EXTM3U\n")
                    for file in selected_files:
                        f.write(str(file.absolute()) + "\n")
                
                self.console.print(f"[success]Playlist {name} byl vytvořen[/success]")
                break
            elif choice == "V":
                selected_indices = set(range(len(files)))
            elif choice == "O":
                selected_indices.clear()
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(files):
                        if index in selected_indices:
                            selected_indices.remove(index)
                        else:
                            selected_indices.add(index)
                    else:
                        self.console.print("[red]Neplatné číslo skladby[/red]")
                except ValueError:
                    self.console.print("[red]Neplatná volba[/red]")

    def _load_playlist(self) -> None:
        """Načtení existujícího playlistu"""
        playlist_dir = self.manager.project_root / "playlists"
        playlists = list(playlist_dir.glob('*.m3u'))
        
        if not playlists:
            self.console.print("[yellow]Žádné playlisty k dispozici[/yellow]")
            return
        
        table = Table(show_header=True)
        table.add_column("č.", justify="right", style="cyan")
        table.add_column("Název", style="white")
        
        for i, playlist in enumerate(playlists, 1):
            table.add_row(str(i), playlist.stem)
        
        self.console.print(table)
        
        choice = Prompt.ask("Vyberte playlist (číslo)")
        try:
            index = int(choice) - 1
            if 0 <= index < len(playlists):
                playlist_file = playlists[index]
                # Načteme skladby z playlistu
                files = []
                with open(playlist_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.startswith('#'):
                            path = Path(line.strip())
                            if path.exists():
                                files.append(path)
                
                if files:
                    self.player.set_playlist(files)
                    self.player.play_file(files[0])
                else:
                    self.console.print("[yellow]Playlist je prázdný nebo obsahuje neexistující soubory[/yellow]")
            else:
                self.console.print("[red]Neplatné číslo playlistu[/red]")
        except ValueError:
            self.console.print("[red]Neplatná volba[/red]")

    def _edit_playlist(self) -> None:
        """Úprava existujícího playlistu"""
        playlist_dir = self.manager.project_root / "playlists"
        playlists = list(playlist_dir.glob('*.m3u'))
        
        if not playlists:
            self.console.print("[yellow]Žádné playlisty k dispozici[/yellow]")
            return
        
        table = Table(show_header=True)
        table.add_column("č.", justify="right", style="cyan")
        table.add_column("Název", style="white")
        
        for i, playlist in enumerate(playlists, 1):
            table.add_row(str(i), playlist.stem)
        
        self.console.print(table)
        
        choice = Prompt.ask("Vyberte playlist k úpravě (číslo)")
        try:
            index = int(choice) - 1
            if 0 <= index < len(playlists):
                playlist_file = playlists[index]
                # Načteme existující skladby
                existing_files = []
                with open(playlist_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.startswith('#'):
                            path = Path(line.strip())
                            if path.exists():
                                existing_files.append(path)
                
                # Spustíme editor playlistu s předvybranými skladbami
                self._create_playlist_with_preselection(playlist_file, existing_files)
            else:
                self.console.print("[red]Neplatné číslo playlistu[/red]")
        except ValueError:
            self.console.print("[red]Neplatná volba[/red]")

    def _create_playlist_with_preselection(self, playlist_file: Path, preselected_files: List[Path]) -> None:
        """Vytvoření/úprava playlistu s předvybranými skladbami"""
        music_dir = Path(self.config['paths']['music_dir'])
        files = list(music_dir.glob('*.mp3'))
        selected_indices = {i for i, f in enumerate(files) if f in preselected_files}
        
        while True:
            self.console.clear()
            table = Table(show_header=True)
            table.add_column("č.", justify="right", style="cyan", width=4)
            table.add_column("Název", style="white")
            table.add_column("Status", justify="center", width=6)
            
            for i, file in enumerate(files, 1):
                status = "[cyan]■[/cyan]" if i-1 in selected_indices else ""
                table.add_row(str(i), file.stem, status)
            
            self.console.print(table)
            
            options = [
                "[cyan]1-{0}[/cyan] Vybrat/zrušit skladbu".format(len(files)),
                "[green]U[/green] Uložit změny",
                "[yellow]V[/yellow] Vybrat vše",
                "[yellow]O[/yellow] Odznačit vše",
                "[red]Z[/red] Zpět"
            ]
            self.console.print("\n".join(options))
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "U":
                if not selected_indices:
                    self.console.print("[yellow]Nejsou vybrány žádné skladby[/yellow]")
                    continue
                
                # Uložíme playlist
                selected_files = [files[i] for i in selected_indices]
                with open(playlist_file, 'w', encoding='utf-8') as f:
                    f.write("#EXTM3U\n")
                    for file in selected_files:
                        f.write(str(file.absolute()) + "\n")
                
                self.console.print(f"[success]Playlist byl aktualizován[/success]")
                break
            elif choice == "V":
                selected_indices = set(range(len(files)))
            elif choice == "O":
                selected_indices.clear()
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(files):
                        if index in selected_indices:
                            selected_indices.remove(index)
                        else:
                            selected_indices.add(index)
                    else:
                        self.console.print("[red]Neplatné číslo skladby[/red]")
                except ValueError:
                    self.console.print("[red]Neplatná volba[/red]")

    def _copy_to_phone(self) -> None:
        """Kopírován hudby do telefonu"""
        # Vytvoříme skryté Tk okno
        root = tk.Tk()
        root.withdraw()
        
        # Dostaneme okno do popředí
        root.lift()
        root.attributes('-topmost', True)
        if os.name == 'nt':
            root.focus_force()
        
        # Otevřeme dialog pro výběr složky, začneme v kořenovém adresáři
        if os.name == 'nt':
            initial_dir = "/"  # Pro Windows zobrazí všechny disky
        else:
            initial_dir = "/media"  # Pro Linux ukáže připojená zařízení
        
        target_dir = filedialog.askdirectory(
            title="Vyberte složku v telefonu",
            initialdir=initial_dir,
            parent=root
        )
        
        root.destroy()
        
        if not target_dir:
            return
        
        target_path = Path(target_dir)
        
        # Načteme všechny hudební soubory a playlisty
        music_dir = Path(self.config['paths']['music_dir'])
        playlist_dir = self.manager.project_root / "playlists"
        
        all_items = []
        
        # Přidáme jednotlivé skladby
        if music_dir.exists():
            for file in music_dir.rglob('*.mp3'):
                rel_path = file.relative_to(music_dir)
                all_items.append(('file', file, rel_path))
            
        # Přidáme playlisty jako složky
        if playlist_dir.exists():
            for playlist in playlist_dir.glob('*.m3u'):
                all_items.append(('playlist', playlist, playlist.stem))
        
        if not all_items:
            self.console.print("[yellow]Žádné soubory k přenosu[/yellow]")
            return
        
        # Zobrazíme seznam položek k výběru
        selected_indices: Set[int] = set()
        
        while True:
            self.console.clear()
            table = Table(show_header=True)
            table.add_column("č.", justify="right", style="cyan", width=4)
            table.add_column("Typ", style="yellow", width=10)
            table.add_column("Název", style="white")
            table.add_column("Status", justify="center", width=6)
            
            for i, (item_type, path, rel_path) in enumerate(all_items, 1):
                status = "[cyan]■[/cyan]" if i-1 in selected_indices else ""
                table.add_row(
                    str(i),
                    "Playlist" if item_type == 'playlist' else "Skladba",
                    str(rel_path),
                    status
                )
            
            self.console.print(table)
            
            # Ovládací menu
            options = [
                "[cyan]1-{0}[/cyan] Vybrat/zrušit položku".format(len(all_items)),
                "[green]K[/green] Kopírovat vybrané položky",
                "[yellow]V[/yellow] Vybrat vše",
                "[yellow]O[/yellow] Odznačit vše",
                "[red]Z[/red] Zpět"
            ]
            self.console.print("\n".join(options))
            
            choice = Prompt.ask("Vyberte možnost").upper()
            
            if choice == "Z":
                break
            elif choice == "K":
                if not selected_indices:
                    self.console.print("[yellow]Nejsou vybrány žádné položky[/yellow]")
                    continue
                
                # Kopírování vybraných položek
                with Progress() as progress:
                    task = progress.add_task("[cyan]Kopíruji...", total=len(selected_indices))
                    
                    for idx in selected_indices:
                        item_type, source_path, rel_path = all_items[idx]
                        
                        if item_type == 'file':
                            # Kopírování jednotlivé skladby
                            dest_path = target_path / rel_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            try:
                                shutil.copy2(source_path, dest_path)
                            except Exception as e:
                                self.console.print(f"[error]Chyba při kopírování {rel_path}: {e}[/error]")
                        
                        elif item_type == 'playlist':
                            # Vytvoření složky pro playlist
                            playlist_folder = target_path / rel_path
                            playlist_folder.mkdir(parents=True, exist_ok=True)
                            
                            # Kopírování skladeb z playlistu
                            try:
                                with open(source_path, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        if not line.startswith('#'):
                                            song_path = Path(line.strip())
                                            if song_path.exists():
                                                dest_path = playlist_folder / song_path.name
                                                shutil.copy2(song_path, dest_path)
                            except Exception as e:
                                self.console.print(f"[error]Chyba při kopírování playlistu {rel_path}: {e}[/error]")
                        
                        progress.update(task, advance=1)
                
                self.console.print("[success]Kopírování dokončeno[/success]")
                break
            
            elif choice == "V":
                selected_indices = set(range(len(all_items)))
            elif choice == "O":
                selected_indices.clear()
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(all_items):
                        if index in selected_indices:
                            selected_indices.remove(index)
                        else:
                            selected_indices.add(index)
                    else:
                        self.console.print("[red]Neplatné číslo položky[/red]")
                except ValueError:
                    self.console.print("[red]Neplatná volba[/red]")

    def _ai_chat(self) -> None:
        """Chat s AI"""
        # Kontrola dostupnosti služeb
        ai_services = {
            "openai": {
                "name": "OpenAI",
                "icon": "🤖",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "active": bool(os.getenv('OPENAI_API_KEY'))
            },
            "ollama": {
                "name": "Ollama",
                "icon": "🦙",
                "models": self._get_local_ollama_models(),
                "active": True
            }
        }

        if not any(v["active"] for v in ai_services.values()):
            self.console.print("[red]Žádná AI služba není dostupná. Nastavte alespoň jeden API klíč.[/red]")
            return

        # Načteme aktuální jazyk
        current_language = self.config.get('ai_chat', {}).get('language', 'cs')
        
        system_messages = {
            "cs": """
        Jsi hudební expert a asistent, který komunikuje výhradně v češtině.
        Máš rozsáhlé znalosti o hudbě, hudebních žánrech, interpretech a skladbách.
        Můžeš doporučovat hudbu, vysvětlovat hudební pojmy a odpovídat na otázky o hudbě.
        Tvé odpovědi jsou přátelské a srozumitelné i pro běžné posluchače.
            """,
            "en": """
            You are a music expert and assistant communicating exclusively in English.
            You have extensive knowledge about music, genres, artists, and songs.
            You can recommend music, explain musical concepts, and answer questions about music.
            Your responses are friendly and understandable for casual listeners.
            """
        }
        
        system_message = system_messages[current_language]
        
        # Historie chatu
        chat_history = []
        
        # Načteme poslední použitou službu a model z konfigurace
        ai_config = self.config.get('ai_chat', {
            'last_service': None,
            'last_model': None
        })

        # Nastavení AI služeb
        ai_services = {
            "openai": {
                "name": "OpenAI",
                "icon": "🤖",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "active": bool(os.getenv('OPENAI_API_KEY'))
            },
            "ollama": {
                "name": "Ollama",
                "icon": "🦙",
                "models": self._get_local_ollama_models(),
                "active": True
            }
        }

        # Výchozí služba - použijeme poslední nebo první dostupnou
        current_service = (
            ai_config['last_service'] 
            if (
                ai_config['last_service'] in ai_services 
                and ai_services[ai_config['last_service']]['active']
            )
            else next((k for k, v in ai_services.items() if v["active"]), None)
        )

        if not current_service:
            self.console.print("[red]Žádná AI služba není dostupná[/red]")
            return

        # Výchozí model - použijeme poslední nebo první dostupný
        current_model = (
            ai_config['last_model'] 
            if ai_config['last_model'] in ai_services[current_service]['models']
            else ai_services[current_service]["models"][0]
        )

        # Počítadla pro OpenAI
        total_cost = 0.0
        total_tokens = 0
        USD_TO_CZK = 23.5

        # Přidáme ceny OpenAI na začátek metody
        openai_prices = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-3.5-turbo": {"input": 0.001 / 1000, "output": 0.002 / 1000}
        }  # Přidána uzavírací závorka

        # Přidáme hudební zkratky
        music_shortcuts = {
            "/p": "přehrát",
            "/s": "similar",
            "/d": "download",
            "/m": "mix",
            "/h": "history",
            "/f": "favorite"
        }

        # Vytvoříme layout s fixní velikostí
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=12),  # Prostor pro informace a příkazy
            Layout(name="chat", ratio=4),    # Historie chatu
            Layout(name="input", size=3)     # Vstupní řádek
        )

        def update_layout():
            # Aktualizace header panelu
            layout["header"].update(Panel(
                "\n".join(header_options),
                title="AI Chat - Nastavení",
                border_style="blue"
            ))

            # Aktualizace chat historie
            if chat_history:
                chat_panel = []
                visible_messages = chat_history[-6:]
                for msg in visible_messages:
                    if msg["role"] == "user":
                        chat_panel.append(f"[bold green]Vy:[/bold green] {msg['content']}")
                    else:
                        chat_panel.append(f"[bold blue]AI:[/bold blue] {msg['content']}")
                
                layout["chat"].update(Panel(
                    "\n\n".join(chat_panel),
                    title="Historie chatu",
                    border_style="green",
                    padding=(0, 1)
                ))
            else:
                layout["chat"].update(Panel(
                    "[dim]Začněte psát pro zahájení konverzace...[/dim]",
                    title="Historie chatu",
                    border_style="green"
                ))

            # Aktualizace příkazů
            commands = [
                "[dim]Příkazy:[/dim]",
                "[cyan]/sluzba[/cyan] [cyan]/model[/cyan] [cyan]/konec[/cyan] [cyan]/smazat[/cyan]",
                "[cyan]/p[/cyan] [cyan]/s[/cyan] [cyan]/d[/cyan] [cyan]/m[/cyan] [cyan]/h[/cyan] [cyan]/f[/cyan]"
            ]
            layout["input"].update(Panel(
                "\n".join(commands),
                title="Vstup",
                border_style="blue"
            ))

        while True:
            self.console.clear()
            
            # Zobrazen�� horního panelu s informacemi
            header_options = [
                f"[bold]Aktivní služba:[/bold] {ai_services[current_service]['icon']} {ai_services[current_service]['name']}",
                f"[bold]Model:[/bold] {current_model}"
            ]
            
            if current_service == "openai":
                credit = self._get_openai_credit()
                if credit:  # Přidáno odsazení pro tento blok
                    header_options.extend([
                        "",
                        "[bold yellow]Statistiky OpenAI:[/bold yellow]",
                        f"Celkem tokenů: {total_tokens:,}",
                        f"Celková cena: {total_cost * USD_TO_CZK:.2f} Kč (${total_cost:.4f})",
                        f"Cena za 1K tokenů: {openai_prices[current_model]['input']*1000*USD_TO_CZK:.2f}/{openai_prices[current_model]['output']*1000*USD_TO_CZK:.2f} Kč",
                        f"Zbývající kredit: {credit['czk']:.2f} Kč (${credit['usd']:.2f})"
                    ])

            # Přidáme nápovědu příkazů
            header_options.extend([
                "",
                "[dim]Příkazy:[/dim]",
                "[cyan]/sluzba[/cyan] - změna AI služby",
                "[cyan]/model[/cyan] - změna modelu",
                "[cyan]/konec[/cyan] - ukončit chat",
                "[cyan]/smazat[/cyan] - smazat historii",
                "[cyan]/p[/cyan] - přehrát doporučenou skladbu",
                "[cyan]/s[/cyan] - najít podobné skladby",
                "[cyan]/d[/cyan] - stáhnout skladbu",
                "[cyan]/m[/cyan] - vytvořit mix",
                "[cyan]/h[/cyan] - historie doporučení"
            ])

            # Zobrazíme panel s informacemi
            self.console.print(Panel("\n".join(header_options), title="AI Chat"))

            # Zobrazíme historii chatu
            if chat_history:
                chat_panel = []
                for msg in chat_history[-6:]:  # Zobrazíme posledních 6 zpráv
                    if msg["role"] == "user":
                        chat_panel.append(f"[bold green]Vy:[/bold green] {msg['content']}")
                    else:
                        chat_panel.append(f"[bold blue]AI:[/bold blue] {msg['content']}")
                
                self.console.print(Panel(
                    "\n\n".join(chat_panel),
                    title="Historie chatu",
                    border_style="green"
                ))

            # Získáme vstup od uživatele
            user_input = Prompt.ask("[bold green]Vy[/bold green]")

            # Zpracování příkazů
            if user_input.startswith("/"):
                cmd = user_input[1:].lower()  # Změníme na jednoduchý string
                
                if cmd == "konec":
                    break
                elif cmd == "smazat":
                    chat_history = []
                    continue
                elif cmd == "sluzba":
                    # Zobrazení dostupných služeb
                    available_services = [k for k, v in ai_services.items() if v["active"]]
                    if not available_services:
                        self.console.print("[red]Žádné další služby nejsou dostupné[/red]")
                        continue
                        
                    self.console.print("\nDostupné služby:")
                    for i, service in enumerate(available_services, 1):
                        service_info = ai_services[service]
                        self.console.print(
                            f"{i}. {service_info['icon']} {service_info['name']}"
                        )
                    
                    choice = Prompt.ask("Vyberte službu (číslo)")
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(available_services):
                            current_service = available_services[idx]
                            current_model = ai_services[current_service]["models"][0]
                            # Reset počtadel při změně služby
                            total_cost = 0.0
                            total_tokens = 0
                    except ValueError:
                        self.console.print("[red]Neplatná volba[/red]")
                    continue
                elif cmd == "model":
                    model = self._show_model_info(
                        service=current_service,
                        current_model=current_model,
                        USD_TO_CZK=USD_TO_CZK
                    )
                    if model:
                        current_model = model
                        # Reset počítadel pro OpenAI
                        if current_service == "openai":
                            total_cost = 0.0
                            total_tokens = 0
                    continue
                elif cmd.startswith("dl "):  # Změníme na startswith pro číslo skladby
                    try:
                        song_idx = int(cmd.split()[1]) - 1
                        if hasattr(self, 'last_songs') and 0 <= song_idx < len(self.last_songs):
                            song = self.last_songs[song_idx]
                            
                            # Vyhledání na YouTube
                            results = self.manager.search_music(f"{song['title']} {song['artist']}")
                            
                            if results:
                                # Zobrazíme výsledky vyhledávání
                                self.console.print("\n[yellow]Nalezené skladby:[/yellow]")
                                downloaded_ids = set()
                                selected_indices = {0}  # Předvybereme první výsledek
                                
                                self.display_results(results, downloaded_ids, selected_indices)
                                
                                # Nabídneme možnosti
                                options = [
                                    "[green]S[/green] Stáhnout vybranou skladbu",
                                    "[yellow]V[/yellow] Vybrat jinou verzi",
                                    "[red]Z[/red] Zpět"
                                ]
                                self.console.print("\n".join(options))
                                
                                while True:
                                    choice = Prompt.ask("Vyberte možnost").upper()
                                    
                                    if choice == "S":
                                        # Stažení vybrané skladby
                                        selected = [results[i] for i in selected_indices][0]
                                        self.console.print(f"[yellow]Stahuji: {selected.title} - {selected.artist}[/yellow]")
                                        self.manager.process_download([selected])
                                        self.console.print("[green]Stažení dokončeno[/green]")
                                        break
                                    elif choice == "V":
                                        # Umožníme vybrat jinou verzi
                                        self.discovery_loop(results)
                                        break
                                    elif choice == "Z":
                                        break
                                    else:
                                        try:
                                            idx = int(choice) - 1
                                            if 0 <= idx < len(results):
                                                selected_indices = {idx}
                                                self.display_results(results, downloaded_ids, selected_indices)
                                            else:
                                                self.console.print("[red]Neplatné číslo skladby[/red]")
                                        except ValueError:
                                            self.console.print("[red]Neplatná volba[/red]")
                        else:
                            self.console.print("[red]Neplatné číslo skladby[/red]")
                    except (ValueError, IndexError):
                        self.console.print("[red]Neplatný formát příkazu. Použijte /dl <číslo>[/red]")
                    continue
                continue  # Pro všechny ostatní příkazy

            # Pokud to není příkaz, zpracujeme jako běžný dotaz
            try:
                with Status("[yellow]AI přemýšlí...[/yellow]", spinner="dots"):
                    if current_service == "openai":
                        # Oprava volání OpenAI API
                        response = self.manager.openai_client.chat.completions.create(
                            model=current_model,
                            messages=[
                                {"role": "system", "content": system_message},
                                *[{"role": m["role"], "content": m["content"]} for m in chat_history],
                                {"role": "user", "content": user_input}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        ai_response = response.choices[0].message.content
                        
                        # Aktualizace statistik pro OpenAI
                        prompt_tokens = response.usage.prompt_tokens
                        completion_tokens = response.usage.completion_tokens
                        cost = (prompt_tokens * openai_prices[current_model]["input"] + 
                               completion_tokens * openai_prices[current_model]["output"])
                        total_cost += cost
                        total_tokens += prompt_tokens + completion_tokens

                    elif current_service == "ollama":
                        try:
                            # Sestavení kontextu z historie
                            context = "\n".join([
                                f"{msg['role']}: {msg['content']}" 
                                for msg in chat_history[-5:]  # Použijeme posledních 5 zpráv
                            ])
                            
                            # Sestavení promptu
                            prompt = f"""Systém: {system_message}

Historie:
{context}

Uživatel: {user_input}
"""
                            
                            response = requests.post(
                                'http://localhost:11434/api/generate',
                                json={
                                    'model': current_model,
                                    'prompt': prompt,
                                    'stream': False
                                }
                            )
                            response.raise_for_status()
                            ai_response = response.json()['response']
                            
                            # Zpracujeme odpověď a přidáme možnosti stažení
                            ai_response = self._process_ai_response(ai_response)
                            
                        except Exception as e:
                            raise ConfigError(f"Chyba při komunikaci s Ollama: {str(e)}")

                    elif current_service == "perplexity":
                        messages = [
                            {"role": "system", "content": system_message},
                            *[{"role": m["role"], "content": m["content"]} for m in chat_history],
                            {"role": "user", "content": user_input}
                        ]
                        ai_response = self.manager.perplexity.generate(
                            "\n".join(m["content"] for m in messages),
                            model=current_model
                        )
                        # Zpracujeme odpověď a přidáme možnosti stažení
                        ai_response = self._process_ai_response(ai_response)

                    elif current_service == "cohere":
                        chat_history_text = "\n".join(f"{m['role']}: {m['content']}" for m in chat_history)
                        response = self.manager.co.chat(
                            message=f"{system_message}\n\nHistorie chatu:\n{chat_history_text}\n\nUživatel: {user_input}",
                            model=current_model,
                            temperature=0.7
                        )
                        ai_response = response.text
                        # Zpracujeme odpověď a přidáme možnosti stažení
                        ai_response = self._process_ai_response(ai_response)

                    # Aktualizace historie
                    chat_history.append({"role": "user", "content": user_input})
                    chat_history.append({"role": "assistant", "content": ai_response})
                    
                    # Omezení délky historie
                    if len(chat_history) > 20:
                        chat_history = chat_history[-20:]
                        
            except Exception as e:
                self.console.print(f"[red]Chyba při komunikaci s AI: {e}[/red]")

    def _process_ai_response(self, response: str) -> str:
        """Zpracuje odpověď od AI a přidá možnosti stažení"""
        songs = []
        lines = response.split('\n')
        
        # Vzory pro detekci skladeb
        patterns = [
            r'(\d+\.\s*)?"([^"]+)"\s+od\s+([^-\n]+)',  # 1. "Název" od Interpret
            r'(\d+\.\s*)?([^"\n]+)\s+od\s+([^-\n]+)',  # 1. Název od Interpret
            r'(\d+\.\s*)?([^"\n]+)\s+-\s+([^-\n]+)',   # 1. Název - Interpret
            r'(\d+\.\s*)?([^"\n]+)\s+by\s+([^-\n]+)'   # 1. Název by Interpret
        ]
        
        for line in lines:
            for pattern in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    try:
                        if len(match) == 3:  # Všechny vzory mají 3 skupiny
                            _, title, artist = match
                            title = title.strip(' "\'')
                            artist = artist.split('(')[0].split('-')[0].strip()
                            
                            if len(title) > 2 and len(artist) > 2:
                                song_info = {
                                    'title': title,
                                    'artist': artist,
                                    'source_text': line.strip()
                                }
                                if not any(s['title'].lower() == title.lower() and 
                                         s['artist'].lower() == artist.lower() for s in songs):
                                    songs.append(song_info)
                    except Exception as e:
                        logging.error(f"Chyba při zpracování řádku '{line}': {e}")
                        continue

        # Přidáme možnosti stažení pod odpověď
        if songs:
            response += "\n\n[yellow]Nalezené skladby ke stažení:[/yellow]"
            for i, song in enumerate(songs, 1):
                response += f"\n{i}. {song['title']} - {song['artist']}"
            response += "\n\n[dim]Dostupné příkazy:[/dim]"
            response += "\n[cyan]/dl <číslo>[/cyan] - stáhnout skladbu"
            response += "\n[cyan]/p <číslo>[/cyan] - přehrát skladbu"
            response += "\n[cyan]/s <číslo>[/cyan] - najít podobné"
            response += "\n[cyan]/m <číslo>[/cyan] - vytvořit mix"
            
            # Uložíme si seznam skladeb pro pozdější stažení
            self.last_songs = songs

        return response

    def _show_model_info(self, service: str, current_model: str = None, USD_TO_CZK: float = 23.5) -> Optional[str]:
        """Zobrazí informace o modelu"""
        if service == "openai":
            # Vytvoříme tabulku pro OpenAI modely
            table = Table(show_header=True)
            table.add_column("č.", justify="right", style="cyan", width=4)
            table.add_column("Model", style="green")
            table.add_column("Cena za 1K tokenů", style="yellow")
            table.add_column("Status", style="blue")

            # Získáme ceny a dostupné modely
            prices = self._get_openai_prices()
            models = ["gpt-4", "gpt-3.5-turbo"]
            
            for i, model in enumerate(models, 1):
                price_info = prices.get(model, {"input": 0, "output": 0})
                price_input = price_info["input"] * 1000 * USD_TO_CZK
                price_output = price_info["output"] * 1000 * USD_TO_CZK
                
                # Zjistíme, jestli je model aktivní
                is_active = model == current_model
                status = "[green]Aktivní[/green]" if is_active else ""
                
                table.add_row(
                    str(i),
                    model,
                    f"Vstup: {price_input:.2f} Kč\nVýstup: {price_output:.2f} Kč",
                    status
                )  # Odstraněn nadbytečný komentář

        elif service == "ollama":
            # Získáme seznamy modelů
            local_models = self._get_local_ollama_models()
            available_models = self._get_available_ollama_models()

            # Vytvoříme tabulku
            table = Table(show_header=True)
            table.add_column("č.", justify="right", style="cyan", width=4)
            table.add_column("Model", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Velikost", style="blue")

            # Nejdřív zobrazíme nainstalované modely
            for i, model in enumerate(local_models, 1):
                info = self._get_ollama_model_info(model)
                size = self._format_size(int(info.get('size', '0')))
                table.add_row(
                    str(i),
                    model,
                    "[green]Nainstalováno[/green]",
                    size
                )

            # Přidáme oddělovač, pokud máme oba typy modelů
            if local_models and available_models:
                table.add_row(
                    "",
                    "─" * 30,
                    "─" * 15,
                    "─" * 10
                )

            # Pak zobrazíme dostupné modely ke stažení
            start_idx = len(local_models) + 1
            for i, model in enumerate(available_models, start_idx):
                if model not in local_models:  # Zobrazíme jen nenainstalované
                    table.add_row(
                        str(i),
                        model,
                        "[yellow]Ke stažení[/yellow]",
                        ""
                    )

            self.console.print("\n[bold]Ollama Modely:[/bold]")
            self.console.print(table)
            self.console.print("\n[dim]Pro stažení modelu použijte /pull <název_modelu>[/dim]")
            self.console.print("[dim]Pro odstranění modelu použijte /remove <název_modelu>[/dim]")

        else:
            # Pro ostatní služby zobrazíme jednoduchý seznam
            models = self.manager.get_available_models(service)
            
            table = Table(show_header=True)
            table.add_column("č.", justify="right", style="cyan", width=4)
            table.add_column("Model", style="green")
            table.add_column("Status", style="blue")
            
            for i, model in enumerate(models, 1):
                is_active = model == current_model
                status = "[green]Aktivní[/green]" if is_active else ""
                table.add_row(str(i), model, status)
            
            self.console.print(f"\n[bold]{service.capitalize()} Modely:[/bold]")
            self.console.print(table)

            # Výběr modelu
            choice = Prompt.ask("Vyberte model (číslo)")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    return models[idx]
            except ValueError:
                self.console.print("[red]Neplatná volba[/red]")

    def _get_local_ollama_models(self) -> List[str]:
        """Získá seznam lokálně nainstalovaných Ollama modelů"""
        try:
            result = subprocess.run(
                ['ollama', 'list'], 
                capture_output=True, 
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')
                # Přeskočíme hlavičku tabulky
                for line in lines[1:]:
                    if line.strip():
                        # První sloupec je název modelu
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            self.console.print(f"[yellow]Chyba při získávání seznamu modelů: {result.stderr}[/yellow]")
            return []
        except Exception as e:
            self.console.print(f"[yellow]Chyba při spouštění ollama list: {e}[/yellow]")
            return []

    def _get_available_ollama_models(self) -> List[str]:
        """Získá seznam dostupných modelů z Ollama Library"""
        try:
            # Použijeme curl pro získání seznamu modelů
            result = subprocess.run(
                ['curl', '-s', 'https://raw.githubusercontent.com/ollama/ollama/main/docs/modelfile.md'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                models = []
                content = result.stdout
                # Hledáme řádky začínající "| `"
                for line in content.split('\n'):
                    if line.startswith('| `') and '`' in line:
                        # Extrahujeme název modelu mezi zpětnými apostrofy
                        model_name = line.split('`')[1]
                        if model_name and not model_name.startswith('FROM'):
                            models.append(model_name)
                return models
            return []
        except Exception as e:
            self.console.print(f"[yellow]Chyba při získávání seznamu dostupných modelů: {e}[/yellow]")
            return []

    def _get_ollama_model_info(self, model: str) -> dict:
        """Získá informace o Ollama modelu"""
        try:
            result = subprocess.run(['ollama', 'show', model], capture_output=True, text=True)
            if result.returncode == 0:
                info = {}
                for line in result.stdout.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                return info
            return {}
        except Exception:
            return {}

    def _format_size(self, size_bytes: Optional[int]) -> str:
        """Formátuje velikost v bytech na čitelný formát"""
        if not size_bytes:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _get_openai_prices(self) -> Dict[str, Dict[str, float]]:
        """Získá aktuální ceny OpenAI modelů"""
        try:
            # Získání cen přes API
            response = self.manager.openai_client.models.list()
            prices = {}
            
            for model in response.data:
                if model.id in ["gpt-4", "gpt-3.5-turbo"]:
                    model_info = self.manager.openai_client.models.retrieve(model.id)
                    prices[model.id] = {
                        "input": model_info.pricing.prompt_tokens,
                        "output": model_info.pricing.completion_tokens
                    }
            
            return prices
            
        except Exception as e:
            # Fallback na pevně dané ceny
            return {
                "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
                "gpt-3.5-turbo": {"input": 0.001 / 1000, "output": 0.002 / 1000}
            }  # Odstraněn nadbytečný komentář

    def _get_genre_recommendation(self, message: str) -> Optional[dict]:
        """Zská doporučení skladby podle kontextu zprávy"""
        genre_file = self.manager.project_root / "data" / "genre_list.json"
        if not genre_file.exists():
            return None
            
        with open(genre_file, 'r', encoding='utf-8') as f:
            genres = json.load(f)
            
        # Zkusíme najít zmínku o žánru v odpovědi
        mentioned_genres = []
        for genre in genres.keys():
            if genre.lower() in message.lower():
                mentioned_genres.append(genre)
        
        if not mentioned_genres:
            # Pokud není zmíněn žádný žánr, vybereme náhodný
            if genres:
                mentioned_genres = [random.choice(list(genres.keys()))]  # Odstraněn nadbytečný komentář
            else:
                return None
        
        # Vybereme náhodnou skladbu z prvního nalezeného žánru
        genre = mentioned_genres[0]
        if genres[genre]:
            return {
                'song': random.choice(genres[genre]),
                'genre': genre
            }
        return None

    def display_image(self, path: Path) -> None:
        """Zobrazí obrázek v terminálu (pouze pro Kitty)"""
        if self.is_kitty:
            try:
                # Použijeme kitty graphics protocol
                os.system(f"kitty +kitten icat {path}")
            except:
                pass

    def show_progress(self, progress: float) -> None:
        """Zobrazí progress bar optimalizovaný pro GPU terminály"""
        if self.is_kitty or self.is_alacritty:
            # Použijeme plynulejší animace
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(pulse_style="cyan"),
                TimeRemainingColumn(),
                refresh_per_second=60  # Vyšší FPS
            ) as progress_bar:
                task = progress_bar.add_task(
                    description="Průběh",
                    total=100
                )
                progress_bar.update(task, completed=int(progress * 100))
                while not progress_bar.finished:
                    progress_bar.refresh()
        else:
            # Základní progress bar pro ostatní terminály
            completed = int(progress * 50)
            bar = f"[{'=' * completed}{' ' * (50 - completed)}] {int(progress * 100)}%"
            self.console.print(bar)

    def _get_available_ollama_models(self) -> List[str]:
        """Získá seznam dostupných modelů z Ollama API"""
        try:
            # Získáme seznam modelů z API
            response = requests.get("https://ollama.ai/api/tags")
            if response.status_code == 200:
                return [model['name'] for model in response.json()]
            return []
        except:
            return []

    def _download_song(self, song_info: Dict[str, str]) -> None:
        """Stáhne skladbu s progress barem"""
        try:
            with Progress() as progress:
                task = progress.add_task(
                    f"[yellow]Stahuji: {song_info['title']} - {song_info['artist']}",
                    total=100
                )
                
                def progress_callback(d):
                    if d['status'] == 'downloading':
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes', 0)
                        if total:
                            progress.update(task, completed=(downloaded/total)*100)

                download_opts = self.manager.ydl_opts.copy()
                download_opts.update({
                    'progress_hooks': [progress_callback]
                })
                
                if 'url' in song_info:
                    # Přímé stažení pomocí URL
                    with yt_dlp.YoutubeDL(download_opts) as ydl:
                        ydl.download([song_info['url']])
                else:
                    # Vyhledání a stažení
                    query = f"{song_info['title']} {song_info['artist']}"
                    results = self.manager.search_music(query)
                    if results:
                        self.manager.process_download([results[0]])
                    else:
                        raise Exception("Skladba nebyla nalezena")
                    
            self.console.print(f"[green]Staženo: {song_info['title']}[/green]")
            self._save_recommendation(song_info, "Staženo z chatu")
            
        except Exception as e:
            self.console.print(f"[red]Chyba při stahování: {e}[/red]")
            self.console.print("[yellow]Zkouším alternativní metodu...[/yellow]")
            try:
                query = f"{song_info['title']} {song_info['artist']} official"
                results = self.manager.search_music(query)
                if results:
                    self.manager.process_download([results[0]])
                    self.console.print("[green]Stažení dokončeno[/green]")
                else:
                    self.console.print("[red]Skladbu se nepodařilo najít[/red]")
            except Exception as e:
                self.console.print(f"[red]Stahování selhalo: {e}[/red]")

    def _save_recommendation(self, song_info: Dict[str, str], context: str) -> None:
        """Uloží doporučení do historie"""
        history = self.config.setdefault('ai_chat', {}).setdefault('recommendation_history', [])
        history.append({
            'title': song_info['title'],
            'artist': song_info['artist'],
            'context': context,
            'timestamp': time.time()
        })
        
        # Omezíme velikost historie
        if len(history) > 50:
            history = history[-50:]
        
        self.config['ai_chat']['recommendation_history'] = history
        self.save_config()

    def _show_recommendation_history(self) -> None:
        """Zobrazí historii doporučení"""
        history = self.config.get('ai_chat', {}).get('recommendation_history', [])
        
        if not history:
            self.console.print("[yellow]Historie doporučení je prázdná[/yellow]")
            return
            
        table = Table(show_header=True)
        table.add_column("č.", justify="right", style="cyan", width=4)
        table.add_column("Skladba", style="green")
        table.add_column("Kontext", style="yellow")
        table.add_column("Čas", style="blue")
        
        for i, rec in enumerate(reversed(history[-10:]), 1):
            timestamp = datetime.fromtimestamp(rec['timestamp']).strftime('%d.%m. %H:%M')
            table.add_row(
                str(i),
                f"{rec['title']} - {rec['artist']}",
                rec['context'][:50] + "..." if len(rec['context']) > 50 else rec['context'],
                timestamp
            )
        
        self.console.print(Panel(table, title="Historie doporučení"))

    def _extract_songs(self, text: str) -> List[Dict[str, str]]:
        """Extrahuje skladby z textu AI odpovědi"""
        songs = []
        lines = text.split('\n')
        
        patterns = [
            r'"([^"]+)"\s+od\s+([^-\n]+)',  # "Název" od Interpret
            r'([^"]+)\s+od\s+([^-\n]+)',    # Název od Interpret (bez uvozovek)
            r'([^-\n]+)\s+by\s+([^-\n]+)',  # Název by Interpret
            r'([^-\n]+)\s+-\s+([^-\n]+)',   # Název - Interpret
            r'(\d+\.\s+)?([^"]+)\s+od\s+([^-\n]+)', # 1. Název od Interpret
            r'(\d+\.\s+)?"([^"]+)"\s+od\s+([^-\n]+)' # 1. "Název" od Interpret
        ]
        
        for line in lines:
            for pattern in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    try:
                        if len(match) == 2:  # Základní vzory
                            title, artist = match
                        elif len(match) == 3:  # Vzory s číslováním
                            if match[0]:  # Pokud je číslo
                                title, artist = match[1], match[2]
                            else:
                                title, artist = match[1], match[2]
                        else:
                            continue

                        # Vyčištění textu
                        title = title.strip(' "\'')
                        artist = artist.split('-')[0].strip()
                        
                        # Přidáme pouze pokud ještě nemáme
                        song_info = {
                            'title': title,
                            'artist': artist,
                            'source_text': line.strip()
                        }
                        if not any(s['title'].lower() == title.lower() and s['artist'].lower() == artist.lower() for s in songs):
                            songs.append(song_info)
                    except Exception as e:
                        print(f"Chyba při zpracování skladby: {e}")
                        continue

        # Přidáme možnosti stažení pod odpověď
        if songs:
            response += "\n\n[yellow]Nalezené skladby ke stažení:[/yellow]"
            for i, song in enumerate(songs, 1):
                response += f"\n{i}. {song['title']} - {song['artist']}"
            response += "\n[dim]Pro stažení použijte příkaz /dl <číslo skladby>[/dim]"
            
            # Uložíme si seznam skladeb pro pozdější stažení
            self.last_songs = songs

        return response

    def _webshare_menu(self) -> None:
        """Menu pro stahování z Webshare"""
        try:
            # Kontrola konfigurace
            ws_config = self.config.get('webshare', {})
            
            # Pokud máme uložené údaje a enabled je False, zkusíme se přihlásit
            if ws_config.get('username') and ws_config.get('password') and not ws_config.get('enabled'):
                try:
                    ws = WebshareDownloader(
                        ws_config['username'],
                        ws_config['password']
                    )
                    # Pokud se přihlášení podařilo, nastavíme enabled na True
                    self.config['webshare']['enabled'] = True
                    self.save_config()
                except Exception as e:
                    self.console.print(f"[red]Chyba při přihlášení: {e}[/red]")
                    if not self._setup_webshare():
                        return
            # Pokud nemáme údaje nebo enabled je False
            elif not ws_config.get('enabled'):
                if not self._setup_webshare():
                    return

            # Inicializace Webshare
            ws = WebshareDownloader(
                ws_config['username'],
                ws_config['password']
            )
            
            while True:
                options = [
                    "[green]1.[/green] Vyhledat skladby",
                    "[green]2.[/green] Stáhnout podle ID",
                    "[green]3.[/green] Nastavení Webshare",
                    "[red]Z.[/red] Zpět"
                ]
                
                self.console.print(Panel("\n".join(options), title="Webshare Stahování"))
                choice = Prompt.ask("Vyberte možnost").upper()
                
                if choice == "Z":
                    break
                elif choice == "1":
                    query = Prompt.ask("Zadejte hledaný výraz")
                    try:
                        results = ws.search(query)
                        if not results:
                            self.console.print("[yellow]Žádné výsledky[/yellow]")
                            continue
                        
                        # Zobrazení výsledků
                        table = Table(show_header=True)
                        table.add_column("č.", justify="right", style="cyan", width=4)
                        table.add_column("Název", style="white")
                        table.add_column("Velikost", style="yellow")
                        table.add_column("ID", style="blue")
                        
                        for i, file in enumerate(results, 1):
                            table.add_row(
                                str(i),
                                file.get('name', 'N/A'),
                                ws.format_size(int(file.get('size', 0))),
                                file.get('ident', 'N/A')
                            )
                        
                        self.console.print(table)
                        
                        # Výběr ke stažení
                        choice = Prompt.ask("Vyberte číslo skladby ke stažení (nebo Z pro zpět)")
                        if choice.upper() == "Z":
                            continue
                        
                        try:
                            idx = int(choice) - 1
                            if 0 <= idx < len(results):
                                file = results[idx]
                                output_dir = Path(self.config['paths']['music_dir'])
                                ws.download_file(file['ident'], output_dir)
                                self.console.print("[green]Stažení dokončeno[/green]")
                            else:
                                self.console.print("[red]Neplatné číslo skladby[/red]")
                        except ValueError:
                            self.console.print("[red]Neplatná volba[/red]")
                        
                    except ConfigError as e:
                        self.console.print(f"[red]{str(e)}[/red]")
                        
                elif choice == "2":
                    file_id = Prompt.ask("Zadejte ID souboru")
                    try:
                        output_dir = Path(self.config['paths']['music_dir'])
                        ws.download_file(file_id, output_dir)
                        self.console.print("[green]Stažení dokončeno[/green]")
                    except ConfigError as e:
                        self.console.print(f"[red]{str(e)}[/red]")
                        
                elif choice == "3":
                    self._setup_webshare()
                    
        except ConfigError as e:
            self.console.print(f"[red]Chyba Webshare: {str(e)}[/red]")

    def _setup_webshare(self) -> bool:
        """Nastavení Webshare účtu"""
        self.console.print("\n[bold]Nastavení Webshare účtu[/bold]")
        
        # Použijeme existující údaje jako výchozí hodnoty
        ws_config = self.config.get('webshare', {})
        default_username = ws_config.get('username', '')
        
        username = Prompt.ask("Zadejte uživatelské jméno", default=default_username)
        password = Prompt.ask("Zadejte heslo", password=True)
        
        try:
            # Test přihlášení
            ws = WebshareDownloader(username, password)
            
            # Uložení konfigurace
            self.config['webshare'] = {
                'username': username,
                'password': password,
                'enabled': True
            }
            self.save_config()
            
            self.console.print("[green]Nastavení Webshare bylo uloženo[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Chyba při nastavení Webshare: {str(e)}[/red]")
            return False

    def _get_openai_credit(self) -> Optional[Dict[str, float]]:
        """Získá zbývající kredit na OpenAI účtu"""
        try:
            response = requests.get(
                "https://api.openai.com/dashboard/billing/credit_grants",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Vrátí kredit v USD a CZK
            usd = data.get('total_available', 0)
            return {
                'usd': usd,
                'czk': usd * USD_TO_CZK
            }
        except Exception as e:
            self.console.print(f"[yellow]Nepoda��ilo se získat informace o kreditu: {e}[/yellow]")
            return None

    def _first_run_wizard(self) -> None:
        """Průvodce prvním spuštěním"""
        self.console.print(Panel(
            "[bold green]Vítejte v YTBAI![/bold green]\n\n"
            "Tento průvodce vám pomůže s počáteční konfigurací.\n"
        ))
        
        # 1. Nastavení složky pro stahování
        self.console.print("\n[bold]1. Složka pro stahování[/bold]")
        default_dir = Path.home() / "Music" / "YouTube"
        music_dir = Prompt.ask(
            "Zadejte cestu ke složce pro stahování",
            default=str(default_dir)
        )
        music_path = Path(music_dir)
        music_path.mkdir(parents=True, exist_ok=True)
        
        # 2. Nastavení AI služeb
        self.console.print("\n[bold]2. AI služby[/bold]")
        self.console.print("""
Pro plnou funkčnost můžete nastavit následující služby:

[green]1. OpenAI[/green] - Nejlepší doporučení (vyžaduje API klíč)
[green]2. Ollama[/green] - Lokální AI (zdarma, vyžaduje instalaci)
[green]3. Další služby[/green] - Cohere, Perplexity, atd.
        """)
        
        # Instrukce pro Ollama
        self.console.print("""
[bold yellow]Instalace Ollama:[/bold yellow]
1. Stáhněte Ollama z [link]https://ollama.ai[/link]
2. Spusťte příkaz: [green]ollama serve[/green]
3. Stáhněte model: [green]ollama pull llama2[/green]
        """)
        
        # Uložení konfigurace
        self.config['paths']['music_dir'] = str(music_path)
        self.config['first_run'] = False
        self.save_config()
        
        self.console.print("\n[bold green]Konfigurace dokončena![/bold green]")

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Centrální zpracování chyb"""
        if isinstance(error, ConfigError):
            self.console.print(f"[red]Chyba konfigurace: {error}[/red]")
        elif isinstance(error, APIError):
            self.console.print(f"[red]Chyba API: {error}[/red]")
        else:
            self.console.print(f"[red]Neočekávaná chyba{f' v {context}' if context else ''}: {error}[/red]")
        logging.error(f"Error in {context}: {error}", exc_info=True)

    def __enter__(self):
        """Context manager pro cleanup"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Automatický cleanup při ukončení"""
        try:
            self._cleanup_all_cache()
            if self.player:
                self.player.cleanup()
        except Exception as e:
            logging.error(f"Chyba při cleanup: {e}")