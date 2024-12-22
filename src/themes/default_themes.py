from typing import Dict

class DefaultThemes:
    """Přednastavené barevné motivy"""
    
    _themes = {
        'dracula': {
            'primary': 'purple',
            'secondary': 'cyan',
            'accent': 'green',
            'warning': 'yellow',
            'error': 'red',
            'border': 'blue',
            'text': 'white',
            'success': 'green',
            'info': 'cyan',
            'muted': 'grey70'
        },
        'nord': {
            'primary': 'blue',
            'secondary': 'cyan',
            'accent': 'green',
            'warning': 'yellow',
            'error': 'red',
            'border': 'blue',
            'text': 'white',
            'success': 'green',
            'info': 'cyan',
            'muted': 'grey70'
        },
        'monokai': {
            'primary': 'magenta',
            'secondary': 'yellow',
            'accent': 'green',
            'warning': 'yellow',
            'error': 'red',
            'border': 'magenta',
            'text': 'white',
            'success': 'green',
            'info': 'cyan',
            'muted': 'grey70'
        }
    }
    
    @classmethod
    def get_theme(cls, name: str) -> Dict[str, str]:
        """Získá téma podle jména"""
        return cls._themes.get(name, cls._themes['dracula'])
        
    @classmethod
    def get_themes(cls) -> Dict[str, Dict[str, str]]:
        """Vrátí všechna dostupná témata"""
        return cls._themes

    @classmethod
    def get_theme_names(cls) -> list[str]:
        """Vrátí seznam názvů dostupných témat"""
        return list(cls._themes.keys())