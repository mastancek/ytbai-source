from rich_icons import Icon, IconSet
from typing import Dict

class IconThemes:
    """Přednastavené sady ikon"""
    
    NERD_FONT = IconSet({
        'name': 'nerd-font',
        'description': 'Nerd Font ikony',
        'icons': {
            'play': '',           # nf-fa-play
            'pause': '',          # nf-fa-pause
            'stop': '',           # nf-fa-stop
            'next': '',           # nf-fa-step_forward
            'prev': '',           # nf-fa-step_backward
            'download': '',       # nf-fa-download
            'search': '',         # nf-fa-search
            'settings': '',       # nf-fa-cog
            'music': '',          # nf-fa-music
            'playlist': '',       # nf-fa-list
            'shuffle': '',        # nf-fa-random
            'repeat': '',         # nf-fa-repeat
            'volume': '',         # nf-fa-volume_up
            'mute': '',          # nf-fa-volume_off
            'heart': '',          # nf-fa-heart
            'star': '★',          # nf-fa-star
            'folder': '',        # nf-fa-folder
            'file': '',          # nf-fa-file
            'trash': '',         # nf-fa-trash
            'edit': '',          # nf-fa-edit
            'save': '',          # nf-fa-save
            'info': '',          # nf-fa-info_circle
            'warning': '',       # nf-fa-warning
            'error': '',         # nf-fa-times_circle
            'success': '',       # nf-fa-check_circle
            'ai': '�',            # nf-md-robot
            'brain': '󰧮',         # nf-md-brain
            'chat': '',          # nf-fa-comments
            'language': '',      # nf-fa-language
            'theme': '',         # nf-fa-paint_brush
            'back': '',          # nf-fa-arrow_left
            'exit': '',          # nf-fa-sign_out
        }
    })

    EMOJI = IconSet({
        'name': 'emoji',
        'description': 'Emoji ikony',
        'icons': {
            'play': '▶️',
            'pause': '⏸️',
            'stop': '⏹️',
            'next': '⏭️',
            'prev': '⏮️',
            'download': '⬇️',
            'search': '🔍',
            'settings': '⚙️',
            'music': '🎵',
            'playlist': '📝',
            'shuffle': '🔀',
            'repeat': '🔁',
            'volume': '🔊',
            'mute': '🔇',
            'heart': '❤️',
            'star': '⭐',
            'folder': '📁',
            'file': '📄',
            'trash': '🗑️',
            'edit': '✏️',
            'save': '💾',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'ai': '🤖',
            'brain': '🧠',
            'chat': '💬',
            'language': '🌐',
            'theme': '🎨',
            'back': '⬅️',
            'exit': '🚪'
        }
    })

    ASCII = IconSet({
        'name': 'ascii',
        'description': 'ASCII ikony (pro terminály bez podpory Unicode)',
        'icons': {
            'play': '>',
            'pause': '||',
            'stop': '[]',
            'next': '>>',
            'prev': '<<',
            'download': 'v',
            'search': 'o-',
            'settings': '*',
            'music': '#',
            'playlist': '=',
            'shuffle': '~',
            'repeat': '@',
            'volume': '}',
            'mute': '{',
            'heart': '<3',
            'star': '*',
            'folder': '[D]',
            'file': '[F]',
            'trash': '[X]',
            'edit': '[E]',
            'save': '[S]',
            'info': '(i)',
            'warning': '(!)',
            'error': '[X]',
            'success': '[V]',
            'ai': '[AI]',
            'brain': '[B]',
            'chat': '[C]',
            'language': '[L]',
            'theme': '[T]',
            'back': '<-',
            'exit': '[Q]'
        }
    })

    @classmethod
    def get_all_sets(cls) -> Dict[str, IconSet]:
        """Vrátí všechny dostupné sady ikon"""
        return {
            'nerd-font': cls.NERD_FONT,
            'emoji': cls.EMOJI,
            'ascii': cls.ASCII
        }

    @classmethod
    def get_set(cls, name: str) -> IconSet:
        """Získá sadu ikon podle jména"""
        sets = cls.get_all_sets()
        return sets.get(name, cls.ASCII)  # Výchozí jsou ASCII ikony 