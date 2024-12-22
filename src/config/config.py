import json
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Načte konfiguraci"""
    config_file = Path.home() / '.ytbai' / 'config.json'
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config: Dict[str, Any]) -> None:
    """Uloží konfiguraci"""
    config_file = Path.home() / '.ytbai' / 'config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2) 