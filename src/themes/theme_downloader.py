import requests
from typing import Dict, Any
from pathlib import Path
import json
import yaml

class ThemeDownloader:
    THEMES_API = "https://raw.githubusercontent.com/tinted-theming/schemes/master/list.yaml"
    THEMES_BASE = "https://raw.githubusercontent.com/tinted-theming/schemes/master/schemes"
    
    def get_available_online_themes(self) -> Dict[str, str]:
        """Získá seznam dostupných online témat"""
        try:
            response = requests.get(self.THEMES_API)
            response.raise_for_status()
            themes = yaml.safe_load(response.text)
            
            theme_list = {}
            for theme in themes:
                theme_list[theme] = f"{self.THEMES_BASE}/{theme}.yaml"
                
            return theme_list
        except Exception as e:
            print(f"Chyba při získávání témat: {e}")
            return {}

    def download_theme(self, theme_name: str) -> Dict[str, str]:
        """Stáhne téma a převede ho do našeho formátu"""
        try:
            url = f"{self.THEMES_BASE}/{theme_name}.yaml"
            response = requests.get(url)
            response.raise_for_status()
            
            base16_theme = yaml.safe_load(response.text)
            
            our_theme = {
                "primary": base16_theme["base0D"],
                "secondary": base16_theme["base0E"],
                "accent": base16_theme["base0B"],
                "error": base16_theme["base08"],
                "success": base16_theme["base0B"],
                "border": base16_theme["base03"],
                "background": base16_theme["base00"],
                "text": base16_theme["base05"]
            }
            
            return our_theme
        except Exception as e:
            print(f"Chyba při stahování tématu: {e}")
            return None

    def save_theme(self, theme_name: str, theme: Dict[str, str]) -> bool:
        """Uloží téma do lokální cache"""
        try:
            cache_dir = Path.home() / ".ytbai" / "themes"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            theme_file = cache_dir / f"{theme_name}.json"
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Chyba při ukládání tématu: {e}")
            return False 