from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any
from rich.prompt import Prompt, Confirm
import json
from datetime import datetime
from ..themes.theme_manager import ThemeManager
from rich.status import Status

class SettingsManager:
    def __init__(self, console: Console, config: Dict[str, Any]):
        self.console = console
        self.config = config
        self.theme_manager = ThemeManager(console, config)
        
    def manage_folders(self):
        """Správa složek"""
        # Přesunout _manage_folders sem
        
    def first_run_wizard(self):
        """Průvodce prvním spuštěním"""
        # Přesunout _first_run_wizard sem

    def manage_ai_services(self):
        """Správa AI služeb"""
        while True:
            try:
                self.console.print("\n[cyan]Správa AI služeb:[/cyan]")
                self.console.print(f"1. OpenAI API")
                self.console.print(f"2. Místní modely")
                self.console.print(f"3. Nastavení API")
                self.console.print(f"4. Testovat připojení")
                self.console.print("Z. Zpět")

                choice = Prompt.ask("Volba").upper()
                if choice == "Z":
                    break
                elif choice == "1":
                    self._configure_openai()
                elif choice == "2":
                    self._configure_local_models()
                elif choice == "3":
                    self._configure_api_settings()
                elif choice == "4":
                    self._test_ai_connections()
            except Exception as e:
                self.console.print(f"[red]Chyba: {e}[/red]")

    def _configure_openai(self):
        """Nastavení OpenAI API"""
        try:
            self.console.print("\n[cyan]OpenAI API Nastavení:[/cyan]")
            api_key = Prompt.ask("API Klíč", password=True)
            model = Prompt.ask(
                "Model",
                choices=["gpt-4", "gpt-3.5-turbo"],
                default=self.config.get('ai_services', {}).get('openai', {}).get('model', 'gpt-3.5-turbo')
            )
            
            if 'ai_services' not in self.config:
                self.config['ai_services'] = {}
            if 'openai' not in self.config['ai_services']:
                self.config['ai_services']['openai'] = {}
                
            self.config['ai_services']['openai'].update({
                'api_key': api_key,
                'model': model
            })
            self.save_config()
            self.console.print("[green]Nastavení uloženo[/green]")
        except Exception as e:
            self.console.print(f"[red]Chyba při ukládání nastavení: {e}[/red]")

    def _configure_local_models(self):
        """Nastavení místních modelů"""
        # TODO: Implementovat nastavení místních modelů

    def _configure_api_settings(self):
        """Obecná nastavení API"""
        # TODO: Implementovat obecná nastavení API

    def _test_ai_connections(self):
        """Test připojení k AI službám"""
        # TODO: Implementovat test připojení

    def show_settings_menu(self):
        """Zobrazí menu nastavení"""
        while True:
            self.console.print("\n[cyan]Nastavení:[/cyan]")
            self.console.print("1. Cesty k souborům")
            self.console.print("2. Kvalita zvuku")
            self.console.print("3. Normalizace hlasitosti")
            self.console.print("4. Konverze formátů")
            self.console.print("5. Metadata")
            self.console.print("6. Cache")
            self.console.print("7. Témata")
            self.console.print("8. Export/Import nastavení")
            self.console.print("Z. Zpět")
            
            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice == "1":
                self._manage_paths()
            elif choice == "2":
                self._configure_audio_quality()
            elif choice == "3":
                self._configure_normalization()
            elif choice == "4":
                self._configure_conversion()
            elif choice == "5":
                self._configure_metadata()
            elif choice == "6":
                self._configure_cache()
            elif choice == "7":
                self._manage_themes()
            elif choice == "8":
                self._manage_config_backup()

    def _configure_audio_quality(self):
        """Nastavení kvality zvuku"""
        self.console.print("\n[cyan]Nastavení kvality zvuku:[/cyan]")
        
        # Kvalita MP3
        quality = Prompt.ask(
            "Kvalita MP3",
            choices=["128", "192", "256", "320"],
            default=self.config.get('audio', {}).get('quality', '192')
        )
        
        if 'audio' not in self.config:
            self.config['audio'] = {}
            
        self.config['audio'].update({
            'quality': quality
        })
        self.save_config()
        self.console.print("[green]Nastavení uloženo[/green]")

    def _configure_normalization(self):
        """Nastavení normalizace hlasitosti pomocí MP3Gain"""
        self.console.print("\n[cyan]Nastavení normalizace hlasitosti:[/cyan]")
        
        # Zapnutí/vypnutí
        enabled = Confirm.ask(
            "Povolit normalizaci?",
            default=self.config.get('audio', {}).get('normalization', {}).get('enabled', True)
        )
        
        if enabled:
            # Typ normalizace
            norm_type = Prompt.ask(
                "Typ normalizace",
                choices=["track", "album", "folder"],
                default=self.config.get('audio', {}).get('normalization', {}).get('type', 'track')
            )
            
            # Target gain (89 dB je standard pro MP3Gain)
            target_gain = "89.0"  # MP3Gain standard
            
            if 'audio' not in self.config:
                self.config['audio'] = {}
            if 'normalization' not in self.config['audio']:
                self.config['audio']['normalization'] = {}
                
            self.config['audio']['normalization'].update({
                'enabled': enabled,
                'type': norm_type,
                'target_gain': float(target_gain)
            })
        else:
            self.config['audio']['normalization'] = {'enabled': False}
            
        self.save_config()
        self.console.print("[green]Nastavení uloženo[/green]")

    def _normalize_folder(self, folder_path: Path):
        """Normalizace celé složky"""
        # TODO: Implementovat normalizaci celé složky pomocí MP3Gain
        # Použít mp3gain.exe -r -k -c na všechny soubory ve složce
        pass

    def _configure_conversion(self):
        """Nastavení konverze formátů"""
        self.console.print("\n[cyan]Nastavení konverze formátů:[/cyan]")
        
        # Výstupní formát
        output_format = Prompt.ask(
            "Výstupní formát",
            choices=["mp3", "m4a", "ogg", "opus"],
            default=self.config.get('conversion', {}).get('output_format', 'mp3')
        )
        
        # Zachovat originál
        keep_original = Confirm.ask(
            "Zachovat originální soubor?",
            default=self.config.get('conversion', {}).get('keep_original', False)
        )
        
        if 'conversion' not in self.config:
            self.config['conversion'] = {}
            
        self.config['conversion'].update({
            'output_format': output_format,
            'keep_original': keep_original
        })
        self.save_config()
        self.console.print("[green]Nastavení uloženo[/green]")

    def _configure_metadata(self):
        """Nastavení metadat"""
        self.console.print("\n[cyan]Nastavení metadat:[/cyan]")
        
        # Cover art
        cover_art = Confirm.ask(
            "Stahovat cover art?",
            default=self.config.get('metadata', {}).get('cover_art', True)
        )
        
        if cover_art:
            # Velikost cover art
            size = Prompt.ask(
                "Velikost cover art (např. 300x300)",
                default=self.config.get('metadata', {}).get('cover_size', '300x300')
            )
            
            # Kvalita JPEG
            quality = Prompt.ask(
                "Kvalita JPEG (0-100)",
                default=str(self.config.get('metadata', {}).get('jpeg_quality', 90))
            )
        
        # Automatické tagy
        auto_tags = Confirm.ask(
            "Automaticky doplňovat tagy?",
            default=self.config.get('metadata', {}).get('auto_tags', True)
        )
        
        if 'metadata' not in self.config:
            self.config['metadata'] = {}
            
        self.config['metadata'].update({
            'cover_art': cover_art,
            'cover_size': size if cover_art else None,
            'jpeg_quality': int(quality) if cover_art else None,
            'auto_tags': auto_tags
        })
        self.save_config()
        self.console.print("[green]Nastavení uloženo[/green]")

    def _configure_cache(self):
        """Nastavení cache"""
        self.console.print("\n[cyan]Nastavení cache:[/cyan]")
        
        # Velikost cache
        cache_size = Prompt.ask(
            "Maximální velikost cache (MB)",
            default=str(self.config.get('cache', {}).get('max_size', 1000))
        )
        
        # Doba platnosti
        cache_ttl = Prompt.ask(
            "Doba platnosti cache (dny)",
            default=str(self.config.get('cache', {}).get('ttl_days', 30))
        )
        
        # Automatické čištění
        auto_clean = Confirm.ask(
            "Automaticky čistit cache?",
            default=self.config.get('cache', {}).get('auto_clean', True)
        )
        
        if 'cache' not in self.config:
            self.config['cache'] = {}
            
        self.config['cache'].update({
            'max_size': int(cache_size),
            'ttl_days': int(cache_ttl),
            'auto_clean': auto_clean
        })
        self.save_config()
        self.console.print("[green]Nastavení uloženo[/green]")

    def _manage_config_backup(self):
        """Správa exportu/importu nastavení"""
        while True:
            self.console.print("\n[cyan]Export/Import nastavení:[/cyan]")
            self.console.print("1. Exportovat nastavení")
            self.console.print("2. Importovat nastavení")
            self.console.print("3. Obnovit výchozí nastavení")
            self.console.print("Z. Zpět")
            
            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice == "1":
                self._export_config()
            elif choice == "2":
                self._import_config()
            elif choice == "3":
                self._reset_config()

    def _export_config(self):
        """Export nastavení do souboru"""
        try:
            backup_dir = Path(self.config['paths']['cache_dir']) / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"config_backup_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
                
            self.console.print(f"[green]Nastavení exportováno do: {backup_file}[/green]")
        except Exception as e:
            self.console.print(f"[red]Chyba při exportu: {e}[/red]")

    def _import_config(self):
        """Import nastavení ze souboru"""
        try:
            backup_dir = Path(self.config['paths']['cache_dir']) / 'backups'
            if not backup_dir.exists():
                self.console.print("[yellow]Žádné zálohy k dispozici[/yellow]")
                return
                
            backups = list(backup_dir.glob('config_backup_*.json'))
            if not backups:
                self.console.print("[yellow]Žádné zálohy k dispozici[/yellow]")
                return
                
            self.console.print("\nDostupné zálohy:")
            for i, backup in enumerate(backups, 1):
                self.console.print(f"{i}. {backup.name}")
                
            choice = Prompt.ask("Vyberte zálohu", choices=[str(i) for i in range(1, len(backups) + 1)])
            selected_backup = backups[int(choice) - 1]
            
            with open(selected_backup, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # Aktualizace konfigurace
            self.config.update(imported_config)
            self.save_config()
            
            self.console.print("[green]Nastavení úspěšně importováno[/green]")
        except Exception as e:
            self.console.print(f"[red]Chyba při importu: {e}[/red]")

    def _reset_config(self):
        """Obnovení výchozího nastavení"""
        if Confirm.ask("Opravdu chcete obnovit výchozí nastavení?", default=False):
            try:
                self.config = self._get_default_config()
                self.save_config()
                self.console.print("[green]Výchozí nastavení obnoveno[/green]")
            except Exception as e:
                self.console.print(f"[red]Chyba při obnovení nastavení: {e}[/red]")

    def _manage_paths(self):
        """Správa cest k souborům"""
        while True:
            self.console.print("\n[cyan]Nastavení cest:[/cyan]")
            self.console.print(f"1. Složka pro stahování: {self.config['paths']['music_dir']}")
            self.console.print(f"2. Cache složka: {self.config['paths']['cache_dir']}")
            self.console.print(f"3. Složka pro logy: {self.config['paths']['logs_dir']}")
            self.console.print("Z. Zpět")
            
            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice in "123":
                path_type = {
                    "1": "music_dir",
                    "2": "cache_dir",
                    "3": "logs_dir"
                }[choice]
                
                # Otevření dialogu pro výběr složky
                root = tk.Tk()
                root.withdraw()  # Skrytí hlavního okna
                
                folder = filedialog.askdirectory(
                    title=f"Vyberte složku pro {path_type}",
                    initialdir=self.config['paths'][path_type]
                )
                
                if folder:  # Pokud byla vybrána složka
                    self.config['paths'][path_type] = str(Path(folder))
                    self.save_config()
                    self.console.print(f"[green]Cesta nastavena na: {folder}[/green]")

    def _configure_theme(self):
        """Nastavení vzhledu aplikace"""
        self.console.print("\n[cyan]Nastavení vzhledu:[/cyan]")
        themes = self.theme_manager.get_available_themes()
        
        for i, theme in enumerate(themes, 1):
            current = "»" if theme == self.config.get('theme') else " "
            self.console.print(f"{current} {i}. {theme.capitalize()}")
        
        choice = Prompt.ask(
            "Vyberte motiv", 
            choices=[str(i) for i in range(1, len(themes) + 1)]
        )
        selected_theme = themes[int(choice) - 1]
        
        with Status("[cyan]Aplikuji téma...[/cyan]"):
            self.theme_manager.apply_theme(selected_theme)
            self.save_config()
        
        # Znovu zobrazíme menu pro okamžitou zpětnou vazbu
        self.show_settings_menu()

    def save_config(self) -> None:
        """Uloží konfiguraci do souboru"""
        try:
            config_file = Path(__file__).parent.parent.parent / 'config' / 'config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
                
        except Exception as e:
            self.console.print(f"[red]Chyba při ukládání konfigurace: {e}[/red]")

    def _get_default_config(self) -> Dict[str, Any]:
        """Vrátí výchozí konfiguraci"""
        return {
            "paths": {
                "music_dir": str(Path.home() / "Music" / "YouTube"),
                "cache_dir": str(Path.home() / ".ytbai" / "cache"),
                "logs_dir": str(Path.home() / ".ytbai" / "logs")
            },
            "audio": {
                "quality": "192k",
                "sample_rate": 44100,
                "bitrate_type": "vbr",
                "normalization": {
                    "enabled": True,
                    "target_level": -16,
                    "true_peak": -1
                }
            },
            "conversion": {
                "output_format": "mp3",
                "keep_original": False
            },
            "metadata": {
                "cover_art": True,
                "cover_size": "300x300",
                "jpeg_quality": 90,
                "auto_tags": True
            },
            "cache": {
                "max_size": 1000,
                "ttl_days": 30,
                "auto_clean": True
            },
            "theme": "dracula",
            "ai_services": {
                "openai": {},
                "cohere": {},
                "huggingface": {},
                "ollama": {}
            }
        }

    def _manage_themes(self):
        """Správa témat"""
        while True:
            self.console.print("\n[cyan]Správa témat:[/cyan]")
            self.console.print("1. Změnit téma")
            self.console.print("2. Upravit barvy")
            self.console.print("3. Stáhnout další témata")
            self.console.print("Z. Zpět")
            
            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice == "1":
                self._configure_theme()
            elif choice == "2":
                self._customize_theme_colors()
            elif choice == "3":
                self.theme_manager.download_themes()