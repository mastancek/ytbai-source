from typing import Optional, Any, Dict, List, Union
from pathlib import Path
import json
import time
import logging
from functools import wraps
import hashlib
from .exceptions import CacheError

class Cache:
    """Třída pro správu cache"""
    def __init__(self, cache_dir: Union[str, Path], max_age: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.max_age = max_age
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializace indexu cache
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Načte index cache ze souboru"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Chyba při načítání indexu cache: {e}")
            return {}

    def _save_index(self) -> None:
        """Uloží index cache do souboru"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logging.error(f"Chyba při ukládání indexu cache: {e}")

    def _get_cache_key(self, key: str) -> str:
        """Vytvoří hash klíče pro cache"""
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Získá hodnotu z cache"""
        try:
            cache_key = self._get_cache_key(key)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                return None
                
            # Kontrola stáří cache
            metadata = self.index.get(cache_key, {})
            if metadata.get('timestamp', 0) + self.max_age < time.time():
                self.invalidate(key)
                return None
                
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logging.error(f"Chyba při čtení z cache: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Uloží hodnotu do cache"""
        try:
            cache_key = self._get_cache_key(key)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(value, f, indent=2)
                
            # Aktualizace indexu
            self.index[cache_key] = {
                'timestamp': time.time(),
                'key': key,
                'size': cache_file.stat().st_size
            }
            self._save_index()
            
        except Exception as e:
            logging.error(f"Chyba při zápisu do cache: {e}")
            raise CacheError(f"Nelze uložit do cache: {str(e)}")

    def invalidate(self, key: str) -> None:
        """Invaliduje položku v cache"""
        try:
            cache_key = self._get_cache_key(key)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if cache_file.exists():
                cache_file.unlink()
                
            if cache_key in self.index:
                del self.index[cache_key]
                self._save_index()
                
        except Exception as e:
            logging.error(f"Chyba při invalidaci cache: {e}")

    def cleanup(self, max_size: int = 100 * 1024 * 1024) -> None:
        """Vyčistí staré položky z cache"""
        try:
            current_size = sum(
                f.stat().st_size for f in self.cache_dir.glob("*.json")
            )
            
            if current_size > max_size:
                # Seřadíme položky podle stáří
                items = sorted(
                    self.index.items(),
                    key=lambda x: x[1]['timestamp']
                )
                
                # Mažeme nejstarší položky
                for cache_key, _ in items:
                    cache_file = self.cache_dir / f"{cache_key}.json"
                    if cache_file.exists():
                        current_size -= cache_file.stat().st_size
                        cache_file.unlink()
                        del self.index[cache_key]
                        
                    if current_size <= max_size:
                        break
                        
                self._save_index()
                
        except Exception as e:
            logging.error(f"Chyba při čištění cache: {e}")

def cached(cache_instance: Cache, ttl: Optional[int] = None):
    """Dekorátor pro cachování výsledků funkcí"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Vytvoření klíče pro cache
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Pokus o získání z cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value
                
            # Výpočet hodnoty
            result = func(*args, **kwargs)
            
            # Uložení do cache
            cache_instance.set(cache_key, result)
            return result
            
        return wrapper
    return decorator 