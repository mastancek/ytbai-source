from dataclasses import dataclass
from typing import Dict

@dataclass
class IconSet:
    """Sada ikon pro UI"""
    name: str
    description: str
    # Základní ikony
    download: str
    play: str
    pause: str
    stop: str
    # Navigační ikony
    back: str
    forward: str
    up: str
    down: str
    # Status ikony
    success: str
    error: str
    warning: str
    info: str
    # Akční ikony
    search: str
    settings: str
    save: str
    delete: str
    edit: str
    # Hudební ikony
    music: str
    playlist: str
    shuffle: str
    repeat: str
    # AI ikony
    ai: str
    brain: str
    magic: str
    # Ostatní ikony
    folder: str
    file: str
    link: str
    key: str
    theme: str
    help: str

class IconSets:
    """Přednastavené sady ikon"""
    
    EMOJI = IconSet(
        name="emoji",
        description="Emoji ikony",
        # Základní ikony
        download="⬇️",
        play="▶️",
        pause="⏸️",
        stop="⏹️",
        # Navigační ikony
        back="↩️",
        forward="↪️",
        up="⬆️",
        down="⬇️",
        # Status ikony
        success="✅",
        error="❌",
        warning="⚠️",
        info="ℹ️",
        # Akční ikony
        search="🔍",
        settings="⚙️",
        save="💾",
        delete="🗑️",
        edit="✏️",
        # Hudební ikony
        music="🎵",
        playlist="📃",
        shuffle="🔀",
        repeat="🔁",
        # AI ikony
        ai="🤖",
        brain="🧠",
        magic="✨",
        # Ostatní ikony
        folder="📁",
        file="📄",
        link="🔗",
        key="🔑",
        theme="🎨",
        help="❓"
    )

    ASCII = IconSet(
        name="ascii",
        description="ASCII ikony",
        # Základní ikony
        download="v",
        play=">",
        pause="||",
        stop="[]",
        # Navigační ikony
        back="<-",
        forward="->",
        up="^",
        down="v",
        # Status ikony
        success="[+]",
        error="[x]",
        warning="[!]",
        info="[i]",
        # Akční ikony
        search="[o]",
        settings="[#]",
        save="[s]",
        delete="[d]",
        edit="[e]",
        # Hudební ikony
        music="♪",
        playlist="=",
        shuffle="~",
        repeat="@",
        # AI ikony
        ai="[AI]",
        brain="[B]",
        magic="*",
        # Ostatní ikony
        folder="/",
        file="-",
        link="&",
        key="K",
        theme="T",
        help="?"
    )

    NERDFONT = IconSet(
        name="nerdfont",
        description="Nerd Font ikony",
        # Základní ikony
        download="",
        play="",
        pause="",
        stop="",
        # Navigační ikony
        back="",
        forward="",
        up="",
        down="",
        # Status ikony
        success="",
        error="",
        warning="",
        info="",
        # Akční ikony
        search="",
        settings="",
        save="",
        delete="",
        edit="",
        # Hudební ikony
        music="",
        playlist="",
        shuffle="",
        repeat="",
        # AI ikony
        ai="",
        brain="",
        magic="",
        # Ostatní ikony
        folder="",
        file="",
        link="",
        key="",
        theme="",
        help=""
    )

    OCTICONS = IconSet(
        name="octicons",
        description="GitHub Octicons styl",
        # Základní ikony
        download="⊼",    # nebo "↓"
        play="▸",        # trojúhelník doprava
        pause="⏸",
        stop="⏹",
        # Navigační ikony
        back="⬅",
        forward="➡",
        up="⬆",
        down="⬇",
        # Status ikony
        success="✔",     # checkmark
        error="✖",       # x mark
        warning="⚠",     # warning
        info="ℹ",        # info
        # Akční ikony
        search="🔍",
        settings="⚙",    # gear
        save="💾",
        delete="🗑",
        edit="✎",        # pencil
        # Hudební ikony
        music="♪",
        playlist="☰",    # list
        shuffle="⇄",
        repeat="↻",
        # AI ikony
        ai="⚡",         # zap
        brain="✨",      # sparkles
        magic="★",       # star
        # Ostatní ikony
        folder="📁",     # folder
        file="📄",       # file
        link="🔗",       # link
        key="🔑",        # key
        theme="🎨",      # palette
        help="❓"        # question
    )

    MARKDOWN = IconSet(
        name="markdown",
        description="GitHub Markdown styl",
        # Základní ikony
        download="⇣",
        play="►",
        pause="⏸",
        stop="⏹",
        # Navigační ikony
        back="←",
        forward="→",
        up="↑",
        down="↓",
        # Status ikony
        success="✓",
        error="✗",
        warning="⚠",
        info="ℹ",
        # Akční ikony
        search="⌕",
        settings="⚙",
        save="⎙",
        delete="⌫",
        edit="✎",
        # Hudební ikony
        music="♬",
        playlist="≡",
        shuffle="⇌",
        repeat="↺",
        # AI ikony
        ai="⚡",
        brain="☆",
        magic="✧",
        # Ostatní ikony
        folder="⌂",
        file="⎗",
        link="⚯",
        key="⚿",
        theme="◑",
        help="?"
    )

    TECHNICAL = IconSet(
        name="technical",
        description="Technické symboly",
        # Základní ikony
        download="⭳",       # šipka dolů v kroužku
        play="▶",          # plný trojúhelník
        pause="⏸",
        stop="⏹",
        # Navigační ikony
        back="◀",          # plný trojúhelník doleva
        forward="▶",       # plný trojúhelník doprava
        up="▲",           # plný trojúhelník nahoru
        down="▼",         # plný trojúhelník dolů
        # Status ikony
        success="✓",      # jednoduchá fajfka
        error="×",        # křížek
        warning="△",      # prázdný trojúhelník
        info="○",         # prázdný kruh
        # Akční ikony
        search="⚲",       # lupa
        settings="⚒",     # kladívka
        save="⎘",         # save symbol
        delete="⌦",       # delete
        edit="✐",         # pero
        # Hudební ikony
        music="♫",        # nota
        playlist="≣",     # tři čáry
        shuffle="⇋",      # šipky
        repeat="↻",       # kruhová šipka
        # AI ikony
        ai="⎈",          # kormidlo/hvězdice
        brain="⌘",       # command symbol
        magic="✧",       # hvězda
        # Ostatní ikony
        folder="⌸",      # složka
        file="⎙",        # dokument
        link="⚯",        # řetěz
        key="⚷",         # klíč
        theme="◐",       # půlměsíc
        help="?"
    )

    SYMBOLS = IconSet(
        name="symbols",
        description="Matematické a logické symboly",
        # Základní ikony
        download="↯",     # blesk dolů
        play="►",        # trojúhelník
        pause="∥",       # dvě čáry
        stop="□",        # čtverec
        # Navigační ikony
        back="���",        # šipka
        forward="→",     # šipka
        up="↑",         # šipka
        down="↓",       # šipka
        # Status ikony
        success="✓",     # fajfka
        error="⨯",      # křížek
        warning="⚠",     # vykřičník v trojúhelníku
        info="ℹ",       # info
        # Akční ikony
        search="⌕",      # lupa
        settings="⚙",    # ozubené kolo
        save="⊗",       # kroužek s křížkem
        delete="∅",      # prázdná množina
        edit="✎",       # tužka
        # Hudební ikony
        music="♪",      # nota
        playlist="≡",   # tři čáry
        shuffle="⇄",    # šipky
        repeat="↺",     # otočit
        # AI ikony
        ai="∆",        # delta/změna
        brain="⊛",     # hvězdice
        magic="∗",     # hvězdička
        # Ostatní ikony
        folder="⌂",     # dům
        file="≝",      # definice
        link="⋈",      # spojení
        key="⚿",       # klíč
        theme="◑",     # měsíc
        help="?"
    )

    GEOMETRIC = IconSet(
        name="geometric",
        description="Geometrické tvary",
        # Základní ikony
        download="▾",    # trojúhelník dolů
        play="▸",       # trojúhelník doprava
        pause="▮▮",     # dva obdélníky
        stop="■",       # čtverec
        # Navigační ikony
        back="◂",       # trojúhelník
        forward="▸",    # trojúhelník
        up="▴",        # trojúhelník
        down="▾",      # trojúhelník
        # Status ikony
        success="●",    # plný kruh
        error="○",     # prázdný kruh
        warning="▲",   # plný trojúhelník
        info="◆",      # kosočtverec
        # Akční ikony
        search="◎",    # kruh s tečkou
        settings="◈",  # kosočtverec
        save="▣",      # čtverec s mřížkou
        delete="▢",    # prázdný čtverec
        edit="✏",      # tužka
        # Hudební ikony
        music="♬",     # noty
        playlist="☰",  # triagram
        shuffle="⬌",   # šipky
        repeat="↻",    # otočit
        # AI ikony
        ai="◇",       # prázdný kosočtverec
        brain="❖",    # kosočtverec s tečkou
        magic="✧",    # hvězda
        # Ostatní ikony
        folder="▤",    # čtverec s mřížkou
        file="▥",     # čtverec s mřížkou
        link="⧉",     # okno
        key="❖",      # kosočtverec
        theme="◐",    # půlkruh
        help="❓"     # otazník
    )

    @classmethod
    def get_all_sets(cls) -> Dict[str, IconSet]:
        """Vrátí všechny dostupné sady ikon"""
        return {
            "emoji": cls.EMOJI,
            "ascii": cls.ASCII,
            "nerdfont": cls.NERDFONT,
            "octicons": cls.OCTICONS,
            "markdown": cls.MARKDOWN,
            "technical": cls.TECHNICAL,
            "symbols": cls.SYMBOLS,
            "geometric": cls.GEOMETRIC
        } 