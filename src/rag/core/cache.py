"""
向量数据库缓存管理器
基于 references/agent_skills 的 Context Optimization 最佳实践

核心功能：
1. Embedding 模型缓存（进程级单例）
2. 向量数据库连接缓存
3. 查询结果缓存（可选，使用 LRU 策略）
"""
import hashlib
import json
import threading
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
)

try:
    from cachetools import LRUCache
    CACHE_TOOLS_AVAILABLE = True
except ImportError:
    CACHE_TOOLS_AVAILABLE = False
    LRUCache = None


class VectorStoreCache:
    """
    向量数据库缓存管理器

    功能：
    1. Embedding 模型缓存（进程级单例）
    2. 向量数据库连接缓存
    3. 查询结果缓存（可选）

    使用场景：
    - 减少 Embedding 模型重复加载
    - 加速向量数据库查询
    - 缓存常见查询结果
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        enable_query_cache: bool = True,
        cache_ttl: int = 3600,  # 缓存有效期（秒），默认 1 小时
        cache_max_size: int = 1000,  # LRU 缓存最大条目数
    ):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录，默认使用 knowledge_base/cache
            enable_query_cache: 是否启用查询结果缓存
            cache_ttl: 缓存有效期（秒）
            cache_max_size: LRU 缓存最大条目数
        """
        self.cache_dir = cache_dir or (CHROMA_PERSIST_DIR / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.enable_query_cache = enable_query_cache
        self.cache_ttl = cache_ttl
        self.cache_max_size = cache_max_size

        # 缓存实例
        self._embedding_model = None
        self._vectorstore = None

        # 使用 LRUCache 替换普通字典，防止内存泄漏
        if CACHE_TOOLS_AVAILABLE:
            self._query_cache = LRUCache(maxsize=cache_max_size)
            print(f"✅ 使用 LRU 缓存（最大: {cache_max_size} 条目）")
        else:
            self._query_cache = {}  # 降级到普通字典
            print(f"⚠️  cachetools 未安装，使用普通字典缓存（无上限）")

        self._cache_metadata = {}  # 缓存元数据：{query_hash: timestamp}
        self._cache_lock = threading.Lock()  # 保护持久化缓存操作的锁

        print(f"✅ 缓存管理器初始化完成（目录: {self.cache_dir}）")

    def get_embedding_model(self):
        """
        懒加载并缓存 Embedding 模型

        Returns:
            LangChain Embeddings 实例
        """
        if self._embedding_model is None:
            from src.rag.config import get_embeddings_cached

            print("📥 正在加载 Embedding 模型...")
            self._embedding_model = get_embeddings_cached()
            print("✅ Embedding 模型已缓存")

        return self._embedding_model

    def get_vectorstore(self):
        """
        懒加载并缓存向量数据库

        Returns:
            Chroma 向量数据库实例
        """
        if self._vectorstore is None:
            from langchain_chroma import Chroma

            print("📥 正在连接向量数据库...")
            self._vectorstore = Chroma(
                persist_directory=str(CHROMA_PERSIST_DIR),
                embedding_function=self.get_embedding_model(),
                collection_name=CHROMA_COLLECTION_NAME,
            )
            print(f"✅ 向量数据库已缓存: {CHROMA_COLLECTION_NAME}")

        return self._vectorstore

    def cache_query_result(
        self,
        query: str,
        results: list,
        context_params: dict = None
    ) -> None:
        """
        缓存查询结果

        Args:
            query: 查询字符串
            results: 查询结果列表
            context_params: 上下文参数（如 top_k, context_mode）
        """
        if not self.enable_query_cache:
            return

        # 生成缓存键（包含查询和参数）
        cache_key = self._generate_cache_key(query, context_params)
        timestamp = datetime.now()

        # 内存缓存（LRU 自动处理上限）
        self._query_cache[cache_key] = (results, timestamp)

        # 持久化缓存（可选）- 需要锁保护
        cache_file = self.cache_dir / f"query_{cache_key}.json"
        try:
            with self._cache_lock:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'results': results,
                        'timestamp': timestamp.isoformat(),
                        'query': query,
                        'params': context_params
                    }, f, ensure_ascii=False)
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"持久化缓存失败: {e}", exc_info=True)

    def get_cached_query(
        self,
        query: str,
        context_params: dict = None
    ) -> Optional[list]:
        """
        获取缓存的查询结果

        Args:
            query: 查询字符串
            context_params: 上下文参数

        Returns:
            缓存的查询结果，如果不存在或已过期则返回 None
        """
        if not self.enable_query_cache:
            return None

        cache_key = self._generate_cache_key(query, context_params)

        # 先检查内存缓存
        if cache_key in self._query_cache:
            results, timestamp = self._query_cache[cache_key]

            # 检查是否过期
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                print(f"🎯 内存缓存命中: {query[:50]}...")
                return results
            else:
                # 过期，删除缓存
                try:
                    del self._query_cache[cache_key]
                except KeyError:
                    pass

        # 检查持久化缓存 - 需要锁保护
        cache_file = self.cache_dir / f"query_{cache_key}.json"
        if cache_file.exists():
            try:
                with self._cache_lock:
                    if not cache_file.exists():
                        return None

                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)

                # 检查是否过期
                cache_time = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cache_time < timedelta(seconds=self.cache_ttl):
                    print(f"🎯 持久化缓存命中: {query[:50]}...")
                    # 加载到内存缓存
                    self._query_cache[cache_key] = (
                        cached_data['results'],
                        cache_time
                    )
                    return cached_data['results']
                else:
                    # 过期，删除缓存文件
                    with self._cache_lock:
                        if cache_file.exists():
                            cache_file.unlink()
            except Exception as e:
                logger = __import__('logging').getLogger(__name__)
                logger.error(f"读取持久化缓存失败: {e}", exc_info=True)

        return None

    def _generate_cache_key(self, query: str, params: dict = None) -> str:
        """
        生成缓存键

        Args:
            query: 查询字符串
            params: 上下文参数

        Returns:
            MD5 哈希值（8 位）
        """
        # 将参数标准化
        if params is None:
            params = {}

        # 生成哈希输入
        hash_input = f"{query}_{sorted(params.items())}"

        # 返回 MD5 哈希的前 8 位
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def clear_cache(self, older_than: int = None) -> int:
        """
        清理缓存

        Args:
            older_than: 清理早于 N 秒的缓存，None 表示清理全部

        Returns:
            清理的缓存数量
        """
        count = 0
        current_time = datetime.now()

        # 清理内存缓存
        if older_than is None:
            count = len(self._query_cache)
            self._query_cache.clear()
        else:
            expired_keys = [
                key for key, (_, timestamp) in self._query_cache.items()
                if (current_time - timestamp).total_seconds() > older_than
            ]
            for key in expired_keys:
                try:
                    del self._query_cache[key]
                    count += 1
                except KeyError:
                    pass

        # 清理持久化缓存
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("query_*.json"):
                try:
                    if older_than is None:
                        with self._cache_lock:
                            if cache_file.exists():
                                cache_file.unlink()
                                count += 1
                    else:
                        # 检查文件修改时间
                        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                        if (current_time - file_time).total_seconds() > older_than:
                            with self._cache_lock:
                                if cache_file.exists():
                                    cache_file.unlink()
                                    count += 1
                except Exception as e:
                    logger = __import__('logging').getLogger(__name__)
                    logger.error(f"删除缓存文件失败: {e}", exc_info=True)

        print(f"🧹 清理了 {count} 个缓存项")
        return count

    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            包含缓存统计的字典
        """
        # 统计持久化缓存文件
        persistent_cache_count = 0
        persistent_cache_size = 0
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("query_*.json"):
                persistent_cache_count += 1
                persistent_cache_size += cache_file.stat().st_size

        return {
            "memory_cache_count": len(self._query_cache),
            "memory_cache_max": self.cache_max_size,
            "persistent_cache_count": persistent_cache_count,
            "persistent_cache_size_mb": round(persistent_cache_size / 1024 / 1024, 2),
            "cache_dir": str(self.cache_dir),
            "query_cache_enabled": self.enable_query_cache,
            "cache_ttl_seconds": self.cache_ttl,
            "using_lru": CACHE_TOOLS_AVAILABLE
        }


# 全局缓存实例
_vector_cache = None
_vector_cache_lock = None


def _get_vector_cache_lock():
    """获取向量缓存初始化锁"""
    global _vector_cache_lock
    if _vector_cache_lock is None:
        _vector_cache_lock = threading.Lock()
    return _vector_cache_lock


def get_vector_cache() -> VectorStoreCache:
    """
    获取全局向量缓存实例（线程安全）

    Returns:
        VectorStoreCache 单例
        线程安全，使用双重检查锁定模式
    """
    global _vector_cache
    if _vector_cache is not None:
        return _vector_cache

    with _get_vector_cache_lock():
        # 双重检查
        if _vector_cache is None:
            _vector_cache = VectorStoreCache()
        return _vector_cache


if __name__ == "__main__":
    # 测试代码
    print("测试 VectorStoreCache")
    cache = VectorStoreCache()

    # 测试缓存统计
    stats = cache.get_cache_stats()
    print(f"\n缓存统计：")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 测试清理缓存（清理早于 1 小时的缓存）
    cache.clear_cache(older_than=3600)
