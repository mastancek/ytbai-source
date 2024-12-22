from typing import Optional, Dict, Any

class YTBAIError(Exception):
    """Základní třída pro YTBAI výjimky"""
    pass

class ConfigError(YTBAIError):
    """Chyba v konfiguraci"""
    pass

class APIError(YTBAIError):
    """Chyba při komunikaci s API"""
    pass

class DownloadError(YTBAIError):
    """Chyba při stahování"""
    pass

class PlaybackError(YTBAIError):
    """Chyba při přehrávání"""
    pass

class AIError(YTBAIError):
    """Chyba v AI službách"""
    pass 