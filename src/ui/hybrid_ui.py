import tkinter as tk
from tkinter import ttk
import platform
from pathlib import Path
import subprocess
from datetime import datetime
import sys
import logging

# Nastavení loggeru pro GUI
logger = logging.getLogger('ytbai.gui')
logger.setLevel(logging.DEBUG)

# Handler pro logování do souboru
gui_handler = logging.FileHandler('ytbai_gui.log')
gui_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(gui_handler)

class HybridUI:
    def __init__(self, root):
        logger.info("Inicializace GUI")
        self.root = root
        self.root.title("YTBAI")
        
        try:
            # Nastavení velikosti okna
            self.root.geometry("1024x768")
            logger.debug("Nastavena velikost okna")
            
            # Rozdělení okna na horní a dolní část
            self.paned = ttk.PanedWindow(root, orient='vertical')
            self.paned.pack(fill='both', expand=True)
            
            # Horní část - terminál
            self.terminal_frame = ttk.Frame(self.paned)
            self._setup_terminal()
            logger.debug("Terminál nastaven")
            
            # Dolní část - prohlížeč souborů
            self.files_frame = ttk.Frame(self.paned)
            self.create_file_browser()
            logger.debug("Prohlížeč souborů vytvořen")
            
            self.paned.add(self.terminal_frame, weight=2)
            self.paned.add(self.files_frame, weight=1)
            
            # Spustit aktualizaci prohlížeče
            self.root.after(1000, self.update_file_browser)
            logger.info("GUI inicializace dokončena")
            
            # Přidáme handler pro ukončení
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
        except Exception as e:
            logger.error(f"Chyba při inicializaci GUI: {e}", exc_info=True)
            raise

    def _setup_terminal(self):
        """Nastaví terminál"""
        try:
            logger.debug("Nastavuji terminál")
            self.terminal_output = tk.Text(
                self.terminal_frame,
                wrap='none',
                font=('Consolas', 10),
                bg='black',
                fg='white'
            )
            self.terminal_output.pack(fill='both', expand=True)
            
            # Scrollbary
            self.terminal_yscroll = ttk.Scrollbar(
                self.terminal_frame,
                command=self.terminal_output.yview
            )
            self.terminal_output['yscrollcommand'] = self.terminal_yscroll.set
            self.terminal_yscroll.pack(side='right', fill='y')
            
            if platform.system() == "Windows":
                self._start_windows_terminal()
                
        except Exception as e:
            logger.error(f"Chyba při nastavení terminálu: {e}", exc_info=True)
            raise

    def _start_windows_terminal(self):
        """Spustí terminál na Windows pomocí pywinpty"""
        try:
            logger.info("Spouštím Windows terminál")
            from winpty import PtyProcess
            
            # Získáme cestu k venv a projektu
            venv_path = Path(sys.executable).parent
            project_path = Path.cwd().parent  # Jdeme o úroveň výš do kořene projektu
            activate_script = venv_path / "Activate.ps1"
            
            logger.debug(f"Cesta k projektu: {project_path}")
            logger.debug(f"Cesta k venv: {venv_path}")
            logger.debug(f"Aktivační skript: {activate_script}")
            
            # Spustit PowerShell
            self.terminal = PtyProcess.spawn('powershell.exe')
            
            # Nastavení prostředí
            self.terminal.write(f"cd '{project_path}'\r\n")  # Přejdeme do kořene projektu
            self.terminal.write(f". '{activate_script}'\r\n")  # Aktivujeme venv
            self.terminal.write(f"$env:PYTHONPATH = '{project_path}'\r\n")  # Nastavíme PYTHONPATH
            
            # Spustit program
            logger.info("Spouštím hlavní program")
            self.terminal.write('python -m src.main\r\n')
            
            def read_output():
                try:
                    if not self.terminal.isalive():
                        logger.warning("Terminál byl ukončen")
                        return
                        
                    data = self.terminal.read()
                    if data:
                        self.terminal_output.insert('end', data)
                        self.terminal_output.see('end')
                        
                except Exception as e:
                    error_msg = f"Chyba při čtení terminálu: {e}"
                    logger.error(error_msg, exc_info=True)
                    if "10053" not in str(e) and "10054" not in str(e):  # Ignorujeme běžné chyby při ukončení
                        self.terminal_output.insert('end', f"\n{error_msg}\n")
                finally:
                    if self.terminal.isalive():  # Pokračujeme jen pokud je terminál živý
                        self.root.after(100, read_output)
            
            read_output()
            logger.debug("Čtení výstupu terminálu spuštěno")
            
        except ImportError as e:
            error_msg = "Pro Windows terminál je potřeba nainstalovat pywinpty: pip install pywinpty"
            logger.error(error_msg)
            self.terminal_output.insert('end', f"{error_msg}\n")
        except Exception as e:
            logger.error(f"Neočekávaná chyba terminálu: {e}", exc_info=True)
            self.terminal_output.insert('end', f"\nNeočekávaná chyba: {e}\n")

    def create_file_browser(self):
        """Vytvoří prohlížeč souborů"""
        # Frame pro ovládací prvky
        self.controls_frame = ttk.Frame(self.files_frame)
        self.controls_frame.pack(fill='x', padx=5, pady=5)
        
        # Tlačítko pro obnovení
        self.refresh_btn = ttk.Button(
            self.controls_frame, 
            text="Obnovit",
            command=self.update_file_browser
        )
        self.refresh_btn.pack(side='left', padx=5)
        
        # Treeview pro zobrazení souborů
        self.file_tree = ttk.Treeview(self.files_frame)
        self.file_tree.pack(side='left', fill='both', expand=True)
        
        # Scrollbar pro strom
        self.tree_scroll = ttk.Scrollbar(
            self.files_frame,
            command=self.file_tree.yview
        )
        self.tree_scroll.pack(side='right', fill='y')
        self.file_tree['yscrollcommand'] = self.tree_scroll.set
        
        # Nastavení sloupců
        self.file_tree['columns'] = ('size', 'modified')
        self.file_tree.heading('#0', text='Název')
        self.file_tree.heading('size', text='Velikost')
        self.file_tree.heading('modified', text='Změněno')
        
        # Šířky sloupců
        self.file_tree.column('#0', width=300)
        self.file_tree.column('size', width=100)
        self.file_tree.column('modified', width=150)

    def update_file_browser(self):
        """Aktualizuje zobrazení souborů"""
        music_dir = Path.home() / "Music" / "YouTube"
        
        # Vyčištění stromu
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
            
        def format_size(size: int) -> str:
            """Formátuje velikost souboru"""
            if size < 1024:
                return f"{size} B"
            elif size < 1024*1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/1024/1024:.1f} MB"
                
        def format_time(timestamp: float) -> str:
            """Formátuje časové razítko"""
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            
        # Naplnění stromu
        def insert_path(parent, path):
            try:
                for item in sorted(path.iterdir()):
                    if item.is_dir():
                        folder_id = self.file_tree.insert(
                            parent, 'end',
                            text=item.name,
                            values=('', format_time(item.stat().st_mtime))
                        )
                        insert_path(folder_id, item)
                    else:
                        self.file_tree.insert(
                            parent, 'end',
                            text=item.name,
                            values=(
                                format_size(item.stat().st_size),
                                format_time(item.stat().st_mtime)
                            )
                        )
            except Exception as e:
                print(f"Chyba při čtení adresáře: {e}")
                
        if music_dir.exists():
            insert_path('', music_dir)
        else:
            self.file_tree.insert('', 'end', text="Složka YouTube Music neexistuje")
        
        # Naplánovat další aktualizaci
        self.root.after(5000, self.update_file_browser)  # Každých 5 sekund
  
    def _on_closing(self):
        """Handler pro ukončení aplikace"""
        try:
            logger.info("Ukončuji aplikaci")
            if hasattr(self, 'terminal'):
                self.terminal.close()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Chyba při ukončování: {e}", exc_info=True)
  