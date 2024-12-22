from typing import List, Dict, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.status import Status
from pathlib import Path
from ..manager.ytbai_manager import YTBAIManager, SearchResult
from ..themes.icons import Icons
from .providers import OpenAIProvider, CohereProvider, HuggingFaceProvider, OllamaProvider

class AIChat:
    def __init__(self, manager: YTBAIManager, console: Console, config: Dict[str, Any]):
        self.manager = manager
        self.console = console
        self.config = config
        self.last_songs = []
        
        # Inicializace AI poskytovatelů
        self.providers = {
            'openai': OpenAIProvider(config),
            'cohere': CohereProvider(config),
            'huggingface': HuggingFaceProvider(config),
            'ollama': OllamaProvider(config)
        }
        self.current_provider = config.get('ai_chat', {}).get('last_provider', 'openai')

    def show_ai_menu(self):
        """Menu pro AI doporučení"""
        while True:
            self.console.print("\n[cyan]AI Asistent:[/cyan]")
            self.console.print("1. Vyhledat podle nálady/žánru")
            self.console.print("2. Najít podobné skladby")
            self.console.print("3. Doporučit na základě historie")
            self.console.print("4. Vygenerovat playlist")
            self.console.print("5. Změnit AI model")
            self.console.print("6. Nastavení AI")
            self.console.print("Z. Zpět")

            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice == "1":
                self._search_by_mood()
            elif choice == "2":
                self._find_similar()
            elif choice == "3":
                self._recommend_from_history()
            elif choice == "4":
                self._generate_playlist()
            elif choice == "5":
                self._change_ai_model()
            elif choice == "6":
                self._configure_ai()

    def _search_by_mood(self):
        """Vyhledávání podle nálady/žánru s využitím AI"""
        prompt = Prompt.ask("Popište náladu nebo žánr hudby")
        
        with Status(f"[cyan]Generuji dotaz pomocí {self.current_provider}...[/cyan]"):
            provider = self.providers[self.current_provider]
            query = provider.generate_query(prompt)
            moods = provider.analyze_mood(prompt)
        
        self.console.print(f"[cyan]Hledám: {query}[/cyan]")
        results = self.manager.search_music(query, limit=15)
        
        if results:
            # Filtrování podle nálady
            filtered_results = [r for r in results if self._matches_mood(r, moods)]
            if filtered_results:
                self.last_songs = filtered_results
                self.manager.ui._process_youtube_results(filtered_results)
            else:
                self.console.print("[yellow]Nenalezeny žádné vhodné skladby[/yellow]")
        else:
            self.console.print("[yellow]Nenalezeny žádné výsledky[/yellow]")

    def _find_similar(self):
        """Najde podobné skladby"""
        song = Prompt.ask("Zadejte název skladby nebo interpreta")
        with Status("[cyan]Hledám podobné skladby...[/cyan]"):
            query = f"mix {song} similar songs"
            results = self.manager.search_music(query, use_related=True)
        
        if results:
            self.last_songs.extend(results[:5])  # Přidáme do historie
            self.manager.ui._process_youtube_results(results)
        else:
            self.console.print("[yellow]Nenalezeny žádné podobné skladby[/yellow]")

    def _recommend_from_history(self):
        """Doporučení na základě historie"""
        if not self.last_songs:
            self.console.print("[yellow]Zatím není dostupná historie poslouchání[/yellow]")
            return
            
        with Status("[cyan]Analyzuji historii a generuji doporučení...[/cyan]"):
            # Vytvoření dotazu z posledních skladeb
            artists = [song.artist for song in self.last_songs[-5:]]
            genres = [song.genre for song in self.last_songs[-5:] if song.genre]
            
            query = f"mix {' '.join(artists)} {' '.join(genres)}"
            results = self.manager.search_music(query, use_recommendations=True)
            
        if results:
            self.manager.ui._process_youtube_results(results)
        else:
            self.console.print("[yellow]Nepodařilo se vygenerovat doporučení[/yellow]")

    def _generate_playlist(self):
        """Generování playlistu"""
        mood = Prompt.ask("Zadejte náladu playlistu")
        length = Prompt.ask("Počet skladeb", default="10")
        
        try:
            count = int(length)
            with Status("[cyan]Generuji playlist...[/cyan]"):
                query = f"playlist {mood} music mix"
                results = self.manager.search_music(query, limit=count, use_playlists=True)
            
            if results:
                self.manager.ui._process_youtube_results(results)
            else:
                self.console.print("[yellow]Nepodařilo se vygenerovat playlist[/yellow]")
        except ValueError:
            self.console.print("[red]Neplatný počet skladeb[/red]")

    def _analyze_library(self):
        """Analýza knihovny"""
        music_dir = Path(self.config['paths']['music_dir'])
        if not music_dir.exists():
            self.console.print("[yellow]Hudební knihovna není dostupná[/yellow]")
            return
            
        with Status("[cyan]Analyzuji knihovnu...[/cyan]"):
            stats = self._get_library_stats()
            
        self._show_library_analysis(stats)

    def _matches_mood(self, result: SearchResult, mood: str) -> bool:
        """Kontroluje, zda skladba odpovídá náladě"""
        # Kontrola v názvu, tazích a popisu
        mood_lower = mood.lower()
        text_to_check = [
            result.title.lower(),
            result.genre.lower() if result.genre else "",
            *[tag.lower() for tag in result.tags]
        ]
        
        return any(mood_lower in text for text in text_to_check)

    def _get_library_stats(self) -> Dict[str, Any]:
        """Získá statistiky knihovny"""
        music_dir = Path(self.config['paths']['music_dir'])
        stats = {
            'total_songs': 0,
            'genres': {},
            'artists': {},
            'years': {},
            'total_duration': 0
        }
        
        for file in music_dir.glob('**/*.mp3'):
            try:
                # TODO: Implementovat analýzu MP3 souborů
                pass
            except Exception as e:
                self.console.print(f"[red]Chyba při analýze {file.name}: {e}[/red]")
                
        return stats

    def _show_library_analysis(self, stats: Dict[str, Any]) -> None:
        """Zobrazí analýzu knihovny"""
        if not stats['total_songs']:
            self.console.print("[yellow]Knihovna je prázdná[/yellow]")
            return
            
        panel = Panel(
            f"""
[bold]Celkem skladeb:[/bold] {stats['total_songs']}
[bold]Celková délka:[/bold] {stats['total_duration'] // 60} minut

[bold]Top žánry:[/bold]
{self._format_top_items(stats['genres'])}

[bold]Top interpreti:[/bold]
{self._format_top_items(stats['artists'])}
""",
            title="Analýza knihovny",
            border_style="cyan"
        )
        self.console.print(panel)

    def _format_top_items(self, items: Dict[str, int], limit: int = 5) -> str:
        """Formátuje top položky pro zobrazení"""
        sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)
        return "\n".join(f"• {name}: {count}" for name, count in sorted_items[:limit])

    def _change_ai_model(self):
        """Změna AI modelu"""
        while True:
            self.console.print("\n[cyan]Výběr AI modelu:[/cyan]")
            for i, (name, provider) in enumerate(self.providers.items(), 1):
                status = "[green]✓[/green]" if provider.get_status() else "[red]✗[/red]"
                current = "[yellow]»[/yellow]" if name == self.current_provider else " "
                self.console.print(f"{current} {i}. {name.capitalize()} {status}")
            self.console.print("Z. Zpět")

            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(self.providers):
                provider_name = list(self.providers.keys())[int(choice)-1]
                if self.providers[provider_name].get_status():
                    self.current_provider = provider_name
                    self.config['ai_chat']['last_provider'] = provider_name
                    self.manager.ui.save_config()
                    self.console.print(f"[green]Model změněn na {provider_name}[/green]")
                else:
                    self.console.print(f"[red]Model {provider_name} není nakonfigurován[/red]")

    def _configure_ai(self):
        """Nastavení AI služeb"""
        while True:
            self.console.print("\n[cyan]Nastavení AI:[/cyan]")
            for i, (name, provider) in enumerate(self.providers.items(), 1):
                status = "[green]✓[/green]" if provider.get_status() else "[red]✗[/red]"
                self.console.print(f"{i}. Konfigurace {name.capitalize()} {status}")
            self.console.print("Z. Zpět")

            choice = Prompt.ask("Volba").upper()
            if choice == "Z":
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(self.providers):
                provider_name = list(self.providers.keys())[int(choice)-1]
                self._configure_provider(provider_name)

    def _configure_provider(self, provider: str):
        """Konfigurace konkrétního AI poskytovatele"""
        if provider == 'openai':
            self._configure_openai()
        elif provider == 'cohere':
            self._configure_cohere()
        elif provider == 'huggingface':
            self._configure_huggingface()
        elif provider == 'ollama':
            self._configure_ollama()

    # ... (pokračovat s dalšími metodami)