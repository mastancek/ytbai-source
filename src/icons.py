from typing import Dict, Any
from icon_sets import IconSets

class Icons:
    """Dynamické ikony podle vybrané sady"""
    _active_set = None

    @classmethod
    def set_active_set(cls, set_name: str) -> None:
        """Nastaví aktivní sadu ikon"""
        cls._active_set = IconSets.get_all_sets().get(set_name)
        if cls._active_set is None:
            cls._active_set = IconSets.get_all_sets()["markdown"]  # fallback

    @classmethod
    def get(cls, name: str) -> str:
        """Získá ikonu z aktivní sady"""
        if cls._active_set is None:
            cls.set_active_set("markdown")  # výchozí sada
        name = name.lower()
        return getattr(cls._active_set, name, "?")

    # Statické atributy jako class properties
    @classmethod
    @property
    def SEARCH(cls) -> str: return cls.get("search")
    
    @classmethod
    @property
    def PLAY(cls) -> str: return cls.get("play")
    
    @classmethod
    @property
    def PAUSE(cls) -> str: return cls.get("pause")
    
    @classmethod
    @property
    def STOP(cls) -> str: return cls.get("stop")
    
    @classmethod
    @property
    def BACK(cls) -> str: return cls.get("back")
    
    @classmethod
    @property
    def FORWARD(cls) -> str: return cls.get("forward")
    
    @classmethod
    @property
    def UP(cls) -> str: return cls.get("up")
    
    @classmethod
    @property
    def DOWN(cls) -> str: return cls.get("down")
    
    @classmethod
    @property
    def SUCCESS(cls) -> str: return cls.get("success")
    
    @classmethod
    @property
    def ERROR(cls) -> str: return cls.get("error")
    
    @classmethod
    @property
    def WARNING(cls) -> str: return cls.get("warning")
    
    @classmethod
    @property
    def INFO(cls) -> str: return cls.get("info")
    
    @classmethod
    @property
    def SETTINGS(cls) -> str: return cls.get("settings")
    
    @classmethod
    @property
    def SAVE(cls) -> str: return cls.get("save")
    
    @classmethod
    @property
    def DELETE(cls) -> str: return cls.get("delete")
    
    @classmethod
    @property
    def EDIT(cls) -> str: return cls.get("edit")
    
    @classmethod
    @property
    def MUSIC(cls) -> str: return cls.get("music")
    
    @classmethod
    @property
    def PLAYLIST(cls) -> str: return cls.get("playlist")
    
    @classmethod
    @property
    def SHUFFLE(cls) -> str: return cls.get("shuffle")
    
    @classmethod
    @property
    def REPEAT(cls) -> str: return cls.get("repeat")
    
    @classmethod
    @property
    def AI(cls) -> str: return cls.get("ai")
    
    @classmethod
    @property
    def BRAIN(cls) -> str: return cls.get("brain")
    
    @classmethod
    @property
    def MAGIC(cls) -> str: return cls.get("magic")
    
    @classmethod
    @property
    def FOLDER(cls) -> str: return cls.get("folder")
    
    @classmethod
    @property
    def FILE(cls) -> str: return cls.get("file")
    
    @classmethod
    @property
    def LINK(cls) -> str: return cls.get("link")
    
    @classmethod
    @property
    def KEY(cls) -> str: return cls.get("key")
    
    @classmethod
    @property
    def THEME(cls) -> str: return cls.get("theme")
    
    @classmethod
    @property
    def HELP(cls) -> str: return cls.get("help")
    
    @classmethod
    @property
    def DOWNLOAD(cls) -> str: return cls.get("download")