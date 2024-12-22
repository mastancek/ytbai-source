import os
from pathlib import Path
import json
import logging
from typing import Any, Dict, Optional
from rich.console import Console
import requests
from PIL import Image
from io import BytesIO
import tiktoken
import time
import hashlib
import numpy as np
import platform
import subprocess
import io
import base64

console = Console()

def setup_logging(log_path: Path) -> None:
    """Nastavení logování"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path / 'ytbai.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: Path) -> Dict[str, Any]:
    """Načte konfiguraci z JSON souboru"""
    try:
        with open(config_path / 'config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        console.print("[yellow]Konfigurace nenalezena, vytvářím výchozí...[/yellow]")
        return create_default_config(config_path)
    except json.JSONDecodeError:
        console.print("[red]Chyba při čtení konfigurace[/red]")
        return create_default_config(config_path)

def create_default_config(config_path: Path) -> Dict[str, Any]:
    """Vytvoří výchozí konfiguraci"""
    config = {
        "paths": {
            "music_dir": str(Path.home() / "Music" / "YouTube"),
            "cache_dir": str(Path.home() / ".ytbai" / "cache"),
            "logs_dir": str(Path.home() / ".ytbai" / "logs")
        },
        "download": {
            "format": "mp3",
            "quality": "192k",
            "max_concurrent": 3
        },
        "api": {
            "openai": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 150,
                "temperature": 0.7
            }
        },
        "ui": {
            "results_per_page": 10,
            "thumbnail_size": [150, 150]
        }
    }
    
    config_path.mkdir(parents=True, exist_ok=True)
    with open(config_path / 'config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    
    return config

def download_and_process_thumbnail(url: str, cache_dir: Path, size: tuple[int, int] = (100, 100)) -> Optional[Path]:
    """Stáhne a zpracuje náhled videa
    
    Args:
        url: URL náhledu
        cache_dir: Adresář pro cache
        size: Požadovaná velikost náhledu (šířka, výška)
        
    Returns:
        Path k uloženému náhledu nebo None při chybě
    """
    try:
        # Vytvoříme hash z URL pro název souboru
        filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
        cache_path = cache_dir / filename
        
        # Pokud existuje v cache, vrátíme ho
        if cache_path.exists():
            return cache_path
            
        # Stáhneme náhled
        response = requests.get(url)
        response.raise_for_status()
        
        # Otevřeme jako obrázek
        img = Image.open(BytesIO(response.content))
        
        # Změníme velikost se zachováním poměru stran
        img.thumbnail(size)
        
        # Vytvoříme nový obrázek s přesnou velikostí a bílým pozadím
        thumb = Image.new('RGB', size, 'white')
        
        # Vypočítáme pozici pro vycentrování
        x = (size[0] - img.width) // 2
        y = (size[1] - img.height) // 2
        
        # Vložíme zmenšený obrázek
        thumb.paste(img, (x, y))
        
        # Uložíme do cache
        thumb.save(cache_path, "JPEG", quality=85)
        return cache_path
        
    except Exception as e:
        logging.error(f"Chyba při zpracování náhledu: {e}")
        return None

def sanitize_filename(filename: str) -> str:
    """Očistí název souboru od neplatných znaků"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def format_duration(seconds: int) -> str:
    """Formátuje délku videa do čitelného formátu"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"

def get_file_size(path: Path) -> str:
    """Vrátí velikost souboru v čitelném formátu"""
    size = path.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB" 

class TokenCostCalculator:
    """Kalkulátor ceny tokenů pro různé AI služby"""
    
    # Kurz USD/CZK
    USD_TO_CZK = 24.17
    
    # Ceny za 1000 tokenů v USD
    PRICES = {
        'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'command': {'input': 0.0015, 'output': 0.0020},  # Cohere
        'llama-2': {'input': 0.0007, 'output': 0.0007},  # Replicate
        'mixtral-8x7b': {'input': 0.0007, 'output': 0.0007}  # Perplexity
    }

    @staticmethod
    def num_tokens_from_string(string: str, model: str = "gpt-3.5-turbo") -> int:
        """Spočítá počet tokenů v textu"""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(string))

    @staticmethod
    def calculate_cost(input_text: str, output_text: str, model: str) -> dict:
        """Vypočítá cenu za použití AI služby"""
        if model not in TokenCostCalculator.PRICES:
            raise ValueError(f"Neznámý model: {model}")
            
        input_tokens = TokenCostCalculator.num_tokens_from_string(input_text, model)
        output_tokens = TokenCostCalculator.num_tokens_from_string(output_text, model)
        
        prices = TokenCostCalculator.PRICES[model]
        input_cost_usd = (input_tokens / 1000) * prices['input']
        output_cost_usd = (output_tokens / 1000) * prices['output']
        total_cost_usd = input_cost_usd + output_cost_usd
        
        # Převod na CZK
        total_cost_czk = total_cost_usd * TokenCostCalculator.USD_TO_CZK
        
        return {
            'total_tokens': input_tokens + output_tokens,
            'total_cost_czk': total_cost_czk
        } 

def cleanup_thumbnail_cache(cache_dir: Path, max_age_hours: int = 24, max_size_mb: int = 100) -> None:
    """Vyčistí cache náhledů"""
    try:
        # Kontrola velikosti cache
        total_size = sum(f.stat().st_size for f in cache_dir.glob('thumb_*.jpg')) / (1024 * 1024)  # v MB
        
        if total_size > max_size_mb:
            logging.info(f"Cache náhledů překročila {max_size_mb}MB, mažu staré soubory...")
            
            # Seřadíme soubory podle času poslední modifikace
            cache_files = sorted(
                cache_dir.glob('thumb_*.jpg'),
                key=lambda x: x.stat().st_mtime
            )
            
            # Mažeme nejstarší soubory, dokud se nedostaneme pod limit
            while total_size > max_size_mb and cache_files:
                oldest_file = cache_files.pop(0)
                file_size = oldest_file.stat().st_size / (1024 * 1024)
                oldest_file.unlink()
                total_size -= file_size
                logging.debug(f"Smazán starý náhled: {oldest_file.name}")

        # Kontrola stáří souborů
        current_time = time.time()
        max_age = max_age_hours * 3600  # převod na sekundy
        
        for thumb_file in cache_dir.glob('thumb_*.jpg'):
            file_age = current_time - thumb_file.stat().st_mtime
            if file_age > max_age:
                thumb_file.unlink()
                logging.debug(f"Smazán starý náhled: {thumb_file.name}")

    except Exception as e:
        logging.error(f"Chyba při čištění cache náhledů: {e}")

def get_image_preview(image_path: Path) -> str:
    """Vytvoří ASCII art náhled z obrázku"""
    try:
        # Načteme obrázek
        img = Image.open(image_path)
        
        # Převedeme na odstíny šedi
        img = img.convert('L')
        
        # Zmenšíme na vhodnou velikost pro terminál (zachováme poměr 2:1 kvůli znakům)
        width = 20
        height = 10
        img = img.resize((width, height))
        
        # Převedeme na numpy array
        pixels = np.array(img)
        
        # ASCII znaky od nejtmavšího po nejsvětlejší
        ascii_chars = '@%#*+=-:. '
        
        # Převedeme hodnoty pixelů na indexy do ascii_chars
        indices = (pixels / 255 * (len(ascii_chars) - 1)).astype(int)
        
        # Vytvoříme ASCII art
        lines = []
        for row in indices:
            line = ''.join(ascii_chars[i] for i in row)
            lines.append(line)
            
        return '\n'.join(lines)
        
    except Exception as e:
        logging.error(f"Chyba při vytváření náhledu: {e}")
        return "♪"

def display_terminal_image(image_path: Path, size: tuple[int, int] = (100, 100)) -> str:
    """Zobrazí obrázek v terminálu podle platformy"""
    system = platform.system().lower()
    
    try:
        img = Image.open(image_path)
        img.thumbnail(size)
        
        if system == "windows":
            # Pro Windows použijeme ASCII art s barvami
            img = img.convert('RGB')
            pixels = np.array(img)
            
            # Vytvoříme barevný ASCII art
            lines = []
            for y in range(0, pixels.shape[0], 2):
                line = ""
                for x in range(pixels.shape[1]):
                    r, g, b = pixels[y, x]
                    # Použijeme ANSI escape sekvence pro barvy
                    line += f"\033[38;2;{r};{g};{b}m█"
                lines.append(line + "\033[0m")  # Reset barvy na konci řádku
            return "\n".join(lines)

        elif system == "linux":
            try:
                import ueberzug.lib.v0 as ueberzug
                with ueberzug.Canvas() as canvas:
                    view = canvas.create_placement(
                        'cover',
                        x=0, y=0,
                        width=size[0],
                        height=size[1],
                        path=str(image_path)
                    )
                    view.visibility = ueberzug.Visibility.VISIBLE
                    return ""
            except ImportError:
                return get_image_preview(image_path)

        elif system == "darwin":
            try:
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_data = base64.b64encode(buffer.getvalue()).decode()
                return f"\033]1337;File=inline=1:{image_data}\a"
            except:
                return get_image_preview(image_path)
                
        return get_image_preview(image_path)
        
    except Exception as e:
        logging.error(f"Chyba při zobrazování obrázku: {e}")
        return "♪"