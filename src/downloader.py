from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio
import logging
from dataclasses import dataclass
from .exceptions import DownloadError
from .retry import retry, DOWNLOAD_RETRY
import yt_dlp
from rich.progress import Progress, TaskID

@dataclass
class DownloadTask:
    """Reprezentace úlohy stahování"""
    video_id: str
    title: str
    output_path: Path
    options: Dict[str, Any]
    progress_callback: Optional[callable] = None

class ParallelDownloader:
    """Třída pro paralelní stahování"""
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_downloads: Dict[str, TaskID] = {}

    @retry(strategy=DOWNLOAD_RETRY)
    async def download_single(self, task: DownloadTask) -> Path:
        """Stažení jednoho souboru"""
        try:
            with yt_dlp.YoutubeDL(task.options) as ydl:
                url = f"https://www.youtube.com/watch?v={task.video_id}"
                info = ydl.extract_info(url, download=True)
                
                if task.progress_callback:
                    task.progress_callback(100)
                    
                return task.output_path / f"{info['title']}.mp3"
        except Exception as e:
            raise DownloadError(f"Chyba při stahování {task.title}", task.video_id, str(e))

    async def download_batch(self, tasks: List[DownloadTask], 
                           progress: Optional[Progress] = None) -> List[Path]:
        """Paralelní stahování více souborů"""
        if not tasks:
            return []

        downloaded_files = []
        task_futures = []

        with Progress() as progress:
            # Vytvoření progress barů pro každý soubor
            for task in tasks:
                task_id = progress.add_task(
                    f"[cyan]Stahuji {task.title}...", 
                    total=100
                )
                self.active_downloads[task.video_id] = task_id
                
                # Vytvoření callback funkce pro aktualizaci progress baru
                def make_callback(task_id):
                    def callback(percent):
                        progress.update(task_id, completed=percent)
                    return callback
                
                task.progress_callback = make_callback(task_id)
                
                # Spuštění stahování v ThreadPoolu
                future = asyncio.create_task(self.download_single(task))
                task_futures.append(future)

            # Čekání na dokončení všech stahování
            try:
                completed_tasks = await asyncio.gather(*task_futures)
                downloaded_files.extend(completed_tasks)
            except Exception as e:
                logging.error(f"Chyba při paralelním stahování: {e}")
                raise

        return downloaded_files

    def cleanup(self):
        """Úklid zdrojů"""
        self.executor.shutdown(wait=True) 