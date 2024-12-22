import os
import platform
from typing import Dict

class ConsoleTheme:
    @staticmethod
    def set_console_colors(theme: Dict[str, str]) -> None:
        """Nastaví barvy konzole podle systému"""
        system = platform.system().lower()
        
        if system == "windows":
            ConsoleTheme._set_windows_colors(theme)
        elif system in ["linux", "darwin"]:
            ConsoleTheme._set_unix_colors(theme)

    @staticmethod
    def _set_windows_colors(theme: Dict[str, str]) -> None:
        """Nastaví barvy pro Windows CMD/PowerShell"""
        try:
            import ctypes
            
            # Mapování barev na Windows color kódy
            color_map = {
                "black": "0",
                "blue": "1",
                "green": "2",
                "cyan": "3",
                "red": "4",
                "purple": "5",
                "yellow": "6",
                "white": "7"
            }
            
            # Získání handle na konzoli
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            
            # Nastavení barev (pozadí << 4 | text)
            bg_color = color_map.get(theme['background'], "0")
            fg_color = color_map.get(theme['text'], "7")
            color_code = int(bg_color) << 4 | int(fg_color)
            
            kernel32.SetConsoleTextAttribute(handle, color_code)
            
            # Vyčištění obrazovky
            os.system('cls')
            
        except Exception:
            pass  # Ignorujeme chyby při nastavování barev

    @staticmethod
    def _set_unix_colors(theme: Dict[str, str]) -> None:
        """Nastaví barvy pro Unix terminály"""
        try:
            # ANSI escape kódy pro barvy
            color_map = {
                "black": "40",
                "red": "41",
                "green": "42",
                "yellow": "43",
                "blue": "44",
                "purple": "45",
                "cyan": "46",
                "white": "47"
            }
            
            text_color_map = {
                "black": "30",
                "red": "31",
                "green": "32",
                "yellow": "33",
                "blue": "34",
                "purple": "35",
                "cyan": "36",
                "white": "37"
            }
            
            # Nastavení barev
            bg_color = color_map.get(theme['background'], "40")
            fg_color = text_color_map.get(theme['text'], "37")
            
            # Escape sekvence pro nastavení barev
            print(f"\033[{fg_color};{bg_color}m", end='')
            
            # Vyčištění obrazovky
            os.system('clear')
            
        except Exception:
            pass  # Ignorujeme chyby při nastavování barev

    @staticmethod
    def reset_colors() -> None:
        """Resetuje barvy konzole na výchozí hodnoty"""
        if platform.system().lower() == "windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)
                kernel32.SetConsoleTextAttribute(handle, 7)  # Výchozí barvy (bílý text na černém pozadí)
            except:
                pass
        else:
            print("\033[0m", end='')  # Reset ANSI barev 