from pathlib import Path
import json
from rich.console import Console
from typing import Dict, Any

console = Console()

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
        "ai_services": {
            "openai": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 300,
                "temperature": 0.7,
                "timeout": 30
            },
            "cohere": {
                "model": "command",
                "max_tokens": 300,
                "temperature": 0.7,
                "timeout": 30
            },
            "perplexity": {
                "model": "mixtral-8x7b-instruct",
                "max_tokens": 300,
                "temperature": 0.7,
                "timeout": 30
            },
            "replicate": {
                "model": "meta/llama-2-70b-chat",
                "max_tokens": 300,
                "temperature": 0.7,
                "timeout": 60
            },
            "huggingface": {
                "model": "facebook/opt-350m",
                "max_tokens": 300,
                "temperature": 0.7,
                "timeout": 30
            }
        },
        "download": {
            "format": "mp3",
            "quality": "192k",
            "max_concurrent": 3
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