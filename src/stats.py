from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict
import logging
from datetime import datetime, timedelta

@dataclass
class DownloadStats:
    """Statistiky stahování"""
    total_downloads: int = 0
    total_size_mb: float = 0
    failed_downloads: int = 0
    average_speed_mbps: float = 0
    total_duration_sec: int = 0

@dataclass
class AIStats:
    """Statistiky využití AI služeb"""
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0
    successful_requests: int = 0
    failed_requests: int = 0

@dataclass
class CacheStats:
    """Statistiky využití cache"""
    hits: int = 0
    misses: int = 0
    total_size_mb: float = 0
    items_count: int = 0

class StatsManager:
    """Správce statistik"""
    def __init__(self, stats_dir: Path):
        self.stats_dir = stats_dir
        self.stats_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.stats_dir / "stats.json"
        
        self.download_stats = DownloadStats()
        self.ai_stats = AIStats()
        self.cache_stats = CacheStats()
        
        self._load_stats()

    def _load_stats(self) -> None:
        """Načte statistiky ze souboru"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.download_stats = DownloadStats(**data.get('downloads', {}))
                    self.ai_stats = AIStats(**data.get('ai', {}))
                    self.cache_stats = CacheStats(**data.get('cache', {}))
        except Exception as e:
            logging.error(f"Chyba při načítání statistik: {e}")

    def _save_stats(self) -> None:
        """Uloží statistiky do souboru"""
        try:
            stats = {
                'downloads': asdict(self.download_stats),
                'ai': asdict(self.ai_stats),
                'cache': asdict(self.cache_stats),
                'last_update': datetime.now().isoformat()
            }
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logging.error(f"Chyba při ukládání statistik: {e}")

    def update_download_stats(self, size_mb: float, duration_sec: int, 
                            success: bool = True) -> None:
        """Aktualizuje statistiky stahování"""
        self.download_stats.total_downloads += 1
        self.download_stats.total_size_mb += size_mb
        self.download_stats.total_duration_sec += duration_sec
        
        if not success:
            self.download_stats.failed_downloads += 1
            
        if duration_sec > 0:
            self.download_stats.average_speed_mbps = (
                size_mb * 8 / duration_sec  # Převod na Mbps
            )
            
        self._save_stats()

    def update_ai_stats(self, tokens: int, cost: float, success: bool = True) -> None:
        """Aktualizuje statistiky AI"""
        self.ai_stats.total_requests += 1
        self.ai_stats.total_tokens += tokens
        self.ai_stats.total_cost += cost
        
        if success:
            self.ai_stats.successful_requests += 1
        else:
            self.ai_stats.failed_requests += 1
            
        self._save_stats()

    def update_cache_stats(self, hit: bool, size_mb: Optional[float] = None) -> None:
        """Aktualizuje statistiky cache"""
        if hit:
            self.cache_stats.hits += 1
        else:
            self.cache_stats.misses += 1
            
        if size_mb is not None:
            self.cache_stats.total_size_mb += size_mb
            self.cache_stats.items_count += 1
            
        self._save_stats()

    def get_summary(self) -> Dict[str, Any]:
        """Vrátí souhrnné statistiky"""
        return {
            'downloads': {
                'total': self.download_stats.total_downloads,
                'success_rate': (
                    (self.download_stats.total_downloads - self.download_stats.failed_downloads) /
                    self.download_stats.total_downloads * 100 if self.download_stats.total_downloads > 0 else 0
                ),
                'total_size_gb': self.download_stats.total_size_mb / 1024,
                'avg_speed_mbps': self.download_stats.average_speed_mbps
            },
            'ai': {
                'total_requests': self.ai_stats.total_requests,
                'success_rate': (
                    self.ai_stats.successful_requests / self.ai_stats.total_requests * 100
                    if self.ai_stats.total_requests > 0 else 0
                ),
                'total_cost': self.ai_stats.total_cost,
                'avg_tokens_per_request': (
                    self.ai_stats.total_tokens / self.ai_stats.total_requests
                    if self.ai_stats.total_requests > 0 else 0
                )
            },
            'cache': {
                'hit_rate': (
                    self.cache_stats.hits / (self.cache_stats.hits + self.cache_stats.misses) * 100
                    if (self.cache_stats.hits + self.cache_stats.misses) > 0 else 0
                ),
                'total_size_mb': self.cache_stats.total_size_mb,
                'items_count': self.cache_stats.items_count
            }
        } 