"""Cache module for storing and retrieving financial data."""

import time
import threading
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class CacheEntry:
    """缓存条目，包含数据和元数据"""
    def __init__(self, data: Any, ttl_seconds: int = 3600):
        self.data = data
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存数据，更新访问统计"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data
    
    def get_size_bytes(self) -> int:
        """估算缓存条目的内存大小"""
        return sys.getsizeof(self.data)

class Cache:
    """增强的内存缓存，支持过期时间、内存管理和性能监控"""

    def __init__(self, max_memory_mb: int = 100, cleanup_interval: int = 300):
        # 缓存存储
        self._prices_cache: Dict[str, CacheEntry] = {}
        self._financial_metrics_cache: Dict[str, CacheEntry] = {}
        self._line_items_cache: Dict[str, CacheEntry] = {}
        self._insider_trades_cache: Dict[str, CacheEntry] = {}
        self._company_news_cache: Dict[str, CacheEntry] = {}
        
        # 缓存配置
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'cleanups': 0
        }
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 启动后台清理线程
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                try:
                    self._cleanup_expired_entries()
                    self._enforce_memory_limit()
                except Exception as e:
                    print(f"缓存清理异常: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_entries(self):
        """清理过期的缓存条目"""
        with self._lock:
            cleaned_count = 0
            
            for cache_dict in [self._prices_cache, self._financial_metrics_cache, 
                             self._line_items_cache, self._insider_trades_cache, 
                             self._company_news_cache]:
                expired_keys = [key for key, entry in cache_dict.items() if entry.is_expired()]
                for key in expired_keys:
                    del cache_dict[key]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self.stats['cleanups'] += 1
                print(f"✓ 清理过期缓存: {cleaned_count} 个条目")
    
    def _enforce_memory_limit(self):
        """强制执行内存限制"""
        current_memory = self._get_total_memory_usage()
        
        if current_memory > self.max_memory_bytes:
            # 收集所有缓存条目及其最后访问时间
            all_entries = []
            
            for cache_name, cache_dict in [
                ('prices', self._prices_cache),
                ('financial_metrics', self._financial_metrics_cache),
                ('line_items', self._line_items_cache),
                ('insider_trades', self._insider_trades_cache),
                ('company_news', self._company_news_cache)
            ]:
                for key, entry in cache_dict.items():
                    all_entries.append((cache_name, key, entry.last_accessed, entry.get_size_bytes()))
            
            # 按最后访问时间排序（最久未访问的优先清理）
            all_entries.sort(key=lambda x: x[2])
            
            # 清理直到内存使用量降到限制以下
            evicted_count = 0
            for cache_name, key, _, size in all_entries:
                if current_memory <= self.max_memory_bytes * 0.8:  # 清理到80%
                    break
                
                cache_dict = getattr(self, f'_{cache_name}_cache')
                if key in cache_dict:
                    del cache_dict[key]
                    current_memory -= size
                    evicted_count += 1
            
            if evicted_count > 0:
                self.stats['evictions'] += evicted_count
                print(f"✓ 内存清理: 移除 {evicted_count} 个缓存条目")
    
    def _get_total_memory_usage(self) -> int:
        """获取总内存使用量"""
        total_size = 0
        for cache_dict in [self._prices_cache, self._financial_metrics_cache,
                          self._line_items_cache, self._insider_trades_cache,
                          self._company_news_cache]:
            for entry in cache_dict.values():
                total_size += entry.get_size_bytes()
        return total_size
    
    def _merge_data(self, existing: list[dict] | None, new_data: list[dict], key_field: str) -> list[dict]:
        """Merge existing and new data, avoiding duplicates based on a key field."""
        if not existing:
            return new_data

        # Create a set of existing keys for O(1) lookup
        existing_keys = {item[key_field] for item in existing}

        # Only add items that don't exist yet
        merged = existing.copy()
        merged.extend([item for item in new_data if item[key_field] not in existing_keys])
        return merged

    def get_prices(self, cache_key: str) -> list[dict[str, any]] | None:
        """Get cached price data if available."""
        with self._lock:
            entry = self._prices_cache.get(cache_key)
            if entry and not entry.is_expired():
                entry.access()
                self.stats['hits'] += 1
                return entry.data
            else:
                self.stats['misses'] += 1
                if entry:  # 过期的条目
                    del self._prices_cache[cache_key]
                return None

    def set_prices(self, cache_key: str, data: list[dict[str, any]], ttl_seconds: int = 3600):
        """Set price data to cache with exact key match."""
        with self._lock:
            self._prices_cache[cache_key] = CacheEntry(data, ttl_seconds)

    def get_financial_metrics(self, cache_key: str) -> list[dict[str, any]] | None:
        """Get cached financial metrics if available."""
        with self._lock:
            entry = self._financial_metrics_cache.get(cache_key)
            if entry and not entry.is_expired():
                entry.access()
                self.stats['hits'] += 1
                return entry.data
            else:
                self.stats['misses'] += 1
                if entry:
                    del self._financial_metrics_cache[cache_key]
                return None

    def set_financial_metrics(self, cache_key: str, data: list[dict[str, any]], ttl_seconds: int = 3600):
        """Set financial metrics to cache with exact key match."""
        with self._lock:
            self._financial_metrics_cache[cache_key] = CacheEntry(data, ttl_seconds)

    def get_line_items(self, cache_key: str) -> list[dict[str, any]] | None:
        """Get cached line items if available."""
        with self._lock:
            entry = self._line_items_cache.get(cache_key)
            if entry and not entry.is_expired():
                entry.access()
                self.stats['hits'] += 1
                return entry.data
            else:
                self.stats['misses'] += 1
                if entry:
                    del self._line_items_cache[cache_key]
                return None

    def set_line_items(self, cache_key: str, data: list[dict[str, any]], ttl_seconds: int = 3600):
        """Set line items to cache with exact key match."""
        with self._lock:
            self._line_items_cache[cache_key] = CacheEntry(data, ttl_seconds)

    def get_insider_trades(self, ticker: str) -> list[dict[str, any]] | None:
        """Get cached insider trades if available."""
        with self._lock:
            entry = self._insider_trades_cache.get(ticker)
            if entry and not entry.is_expired():
                entry.access()
                self.stats['hits'] += 1
                return entry.data
            else:
                self.stats['misses'] += 1
                if entry:
                    del self._insider_trades_cache[ticker]
                return None

    def set_insider_trades(self, ticker: str, data: list[dict[str, any]], ttl_seconds: int = 3600):
        """Append new insider trades to cache."""
        with self._lock:
            existing_data = None
            if ticker in self._insider_trades_cache:
                existing_entry = self._insider_trades_cache[ticker]
                if not existing_entry.is_expired():
                    existing_data = existing_entry.data
            
            merged_data = self._merge_data(existing_data, data, key_field="filing_date")
            self._insider_trades_cache[ticker] = CacheEntry(merged_data, ttl_seconds)

    def get_company_news(self, ticker: str) -> list[dict[str, any]] | None:
        """Get cached company news if available."""
        with self._lock:
            entry = self._company_news_cache.get(ticker)
            if entry and not entry.is_expired():
                entry.access()
                self.stats['hits'] += 1
                return entry.data
            else:
                self.stats['misses'] += 1
                if entry:
                    del self._company_news_cache[ticker]
                return None

    def set_company_news(self, ticker: str, data: list[dict[str, any]], ttl_seconds: int = 3600):
        """Append new company news to cache."""
        with self._lock:
            existing_data = None
            if ticker in self._company_news_cache:
                existing_entry = self._company_news_cache[ticker]
                if not existing_entry.is_expired():
                    existing_data = existing_entry.data
            
            merged_data = self._merge_data(existing_data, data, key_field="date")
            self._company_news_cache[ticker] = CacheEntry(merged_data, ttl_seconds)
    
    def clear_cache(self):
        """Clear all cached data."""
        with self._lock:
            cache_counts = {
                "prices": len(self._prices_cache),
                "financial_metrics": len(self._financial_metrics_cache),
                "line_items": len(self._line_items_cache),
                "insider_trades": len(self._insider_trades_cache),
                "company_news": len(self._company_news_cache)
            }
            
            self._prices_cache.clear()
            self._financial_metrics_cache.clear()
            self._line_items_cache.clear()
            self._insider_trades_cache.clear()
            self._company_news_cache.clear()
            
            # 重置统计信息
            self.stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'cleanups': 0
            }
            
            total_cleared = sum(cache_counts.values())
            print(f"✓ API缓存已清空: {total_cleared} 个缓存项")
            print(f"  - 价格数据: {cache_counts['prices']} 项")
            print(f"  - 财务指标: {cache_counts['financial_metrics']} 项")
            print(f"  - 财务报表: {cache_counts['line_items']} 项")
            print(f"  - 内部交易: {cache_counts['insider_trades']} 项")
            print(f"  - 公司新闻: {cache_counts['company_news']} 项")
            
            return total_cleared
    
    def get_cache_info(self):
        """Get cache information."""
        with self._lock:
            total_memory = self._get_total_memory_usage()
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            
            return {
                'counts': {
                    'prices': len(self._prices_cache),
                    'financial_metrics': len(self._financial_metrics_cache),
                    'line_items': len(self._line_items_cache),
                    'insider_trades': len(self._insider_trades_cache),
                    'company_news': len(self._company_news_cache)
                },
                'memory': {
                    'total_bytes': total_memory,
                    'total_mb': round(total_memory / 1024 / 1024, 2),
                    'limit_mb': round(self.max_memory_bytes / 1024 / 1024, 2),
                    'usage_percent': round((total_memory / self.max_memory_bytes) * 100, 2)
                },
                'stats': {
                    'hit_rate': round(hit_rate * 100, 2),
                    'hits': self.stats['hits'],
                    'misses': self.stats['misses'],
                    'evictions': self.stats['evictions'],
                    'cleanups': self.stats['cleanups']
                },
                "total_count": len(self._prices_cache) + len(self._financial_metrics_cache) + 
                              len(self._line_items_cache) + len(self._insider_trades_cache) + 
                              len(self._company_news_cache)
            }
    
    def get_cache_stats(self) -> str:
        """获取缓存统计信息的格式化字符串"""
        info = self.get_cache_info()
        return f"""缓存统计:
  命中率: {info['stats']['hit_rate']}% ({info['stats']['hits']}/{info['stats']['hits'] + info['stats']['misses']})
  内存使用: {info['memory']['total_mb']}MB / {info['memory']['limit_mb']}MB ({info['memory']['usage_percent']}%)
  缓存条目: 价格({info['counts']['prices']}) 财务({info['counts']['financial_metrics']}) 行项目({info['counts']['line_items']}) 内幕交易({info['counts']['insider_trades']}) 新闻({info['counts']['company_news']})
  清理次数: {info['stats']['cleanups']}, 逐出次数: {info['stats']['evictions']}"""


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache
