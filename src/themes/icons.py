from typing import Dict
import os

class Icons:
    """Centrální správa ikon pro aplikaci"""
    
    _sets = {
        'emoji': {
            'SEARCH': '🔍',
            'AI': '🤖',
            'BRAIN': '🧠',
            'CHAT': '💭',
            'SETTINGS': '⚙️',
            'THEME': '🎨',
            'MUSIC': '🎵',
            'DOWNLOAD': '⬇️',
            'EXIT': '🚪',
            'CHECK': '✓',
            'WARN': '⚠️',
            'ERROR': '❌',
            'INFO': 'ℹ️',
            'PLAY': '▶️',
            'PAUSE': '⏸️',
            'STOP': '⏹️',
            'NEXT': '⏭️',
            'PREV': '⏮️'
        },
        'ascii': {
            'SEARCH': '[S]',
            'AI': '[A]',
            'BRAIN': '[B]',
            'CHAT': '[C]',
            'SETTINGS': '[*]',
            'THEME': '[T]',
            'MUSIC': '[M]',
            'DOWNLOAD': '[D]',
            'EXIT': '[X]',
            'CHECK': '[✓]',
            'WARN': '[!]',
            'ERROR': '[X]',
            'INFO': '[i]',
            'PLAY': '[>]',
            'PAUSE': '[||]',
            'STOP': '[[]',
            'NEXT': '[>>]',
            'PREV': '[<<]'
        }
    }
    
    _active_set = 'emoji'
    
    @classmethod
    def set_active_set(cls, set_name: str):
        if set_name in cls._sets:
            cls._active_set = set_name
            
    @classmethod
    def get(cls, icon_name: str, use_ascii: bool = False) -> str:
        set_name = 'ascii' if use_ascii else cls._active_set
        return cls._sets.get(set_name, {}).get(icon_name, '')

def is_emoji_supported() -> bool:
    """Kontrola podpory emoji v terminálu"""
    if os.name == 'nt':  # Windows
        return os.getenv('WT_SESSION') is not None  # Windows Terminal
    return True  # Unix-like systémy většinou podporují emoji