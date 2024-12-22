from typing import Dict, Any
from pathlib import Path
from .exceptions import ConfigError, ValidationError

def validate_config(config: Dict[str, Any]) -> bool:
    """Validace konfiguračního souboru
    
    Args:
        config: Konfigurační slovník
        
    Returns:
        bool: True pokud je konfigurace validní
        
    Raises:
        ConfigError: Pokud konfigurace není validní
    """
    required_fields = {
        'paths': ['music_dir', 'cache_dir', 'logs_dir'],
        'ai_services': ['openai', 'cohere', 'perplexity', 'replicate', 'huggingface'],
        'download': ['format', 'quality', 'max_concurrent'],
        'ui': ['results_per_page', 'thumbnail_size']
    }
    
    try:
        # Kontrola hlavních sekcí
        for section, fields in required_fields.items():
            if section not in config:
                raise ConfigError(f"Chybí sekce {section}")
            
            # Kontrola povinných polí v každé sekci
            for field in fields:
                if field not in config[section]:
                    raise ConfigError(f"Chybí pole {field} v sekci {section}")
        
        # Validace cest
        for path_key, path_str in config['paths'].items():
            path = Path(path_str)
            if not path.parent.exists():
                raise ConfigError(f"Nadřazená složka pro {path_key} neexistuje: {path_str}")
        
        # Validace hodnot
        if not isinstance(config['download']['max_concurrent'], int):
            raise ConfigError("max_concurrent musí být celé číslo")
        
        if not isinstance(config['ui']['results_per_page'], int):
            raise ConfigError("results_per_page musí být celé číslo")
        
        if not isinstance(config['ui']['thumbnail_size'], list) or len(config['ui']['thumbnail_size']) != 2:
            raise ConfigError("thumbnail_size musí být seznam dvou čísel")
        
        return True
        
    except Exception as e:
        raise ConfigError(f"Chyba při validaci konfigurace: {str(e)}")

def validate_search_result(result: Dict[str, Any]) -> bool:
    """Validace výsledku vyhledávání
    
    Args:
        result: Slovník s výsledkem vyhledávání
        
    Returns:
        bool: True pokud je výsledek validní
        
    Raises:
        ValidationError: Pokud výsledek není validní
    """
    required_fields = ['title', 'artist', 'duration', 'video_id']
    
    try:
        for field in required_fields:
            if field not in result:
                raise ValidationError(f"Chybí povinné pole {field}")
            
            if not isinstance(result[field], str):
                raise ValidationError(f"Pole {field} musí být řetězec")
            
            if not result[field]:
                raise ValidationError(f"Pole {field} nesmí být prázdné")
        
        return True
        
    except Exception as e:
        raise ValidationError(f"Chyba při validaci výsledku: {str(e)}") 