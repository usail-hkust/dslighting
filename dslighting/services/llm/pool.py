# pool.py

"""
API key pool and connection pool management for LLM services.

Provides:
- GlobalAPIKeyPool: Manages multiple API keys with load balancing and concurrency limits
- LLMConnectionPool: Manages HTTP connection pooling for LLM API requests
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import weakref
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import litellm

from dslighting.utils.constants import (
    DEFAULT_MAX_CONCURRENT_PER_KEY,
    DEFAULT_POOL_SIZE,
    KEEPALIVE_TIMEOUT_SECONDS,
    LLM_HTTP_CLIENT_TIMEOUT,
)

# Try to import aiohttp for connection pooling
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logging.debug("aiohttp not available, HTTP connection pooling disabled")

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class GlobalAPIKeyPool:
    """
    全局共享的 API Key 池，均匀分配负载到所有 keys。

    每个 key 有独立的并发限制，避免单个 key 瞬间并发过高触发 TPM/RPM 限制。
    """

    # 类级别的全局实例（按模型名称分组）
    _pools: dict[str, "GlobalAPIKeyPool"] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        model_name: str,
        keys: list[str],
        max_concurrent_per_key: int = DEFAULT_MAX_CONCURRENT_PER_KEY,
    ):
        """
        初始化全局 Key 池。

        Args:
            model_name: 模型名称（用于区分不同模型的 key 池）
            keys: API key 列表
            max_concurrent_per_key: 每个 key 的最大并发数
        """
        self.model_name = model_name
        self.keys = keys
        self.max_concurrent_per_key = max_concurrent_per_key

        # 每个事件循环都有独立的 key 信号量，避免跨 loop 复用 asyncio 原语
        self._loop_semaphores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, dict[str, asyncio.Semaphore]]" = weakref.WeakKeyDictionary()
        self._semaphore_lock = threading.Lock()

        # 轮询索引（用于负载均衡）
        self.current_index = 0
        self.index_lock = threading.Lock()

        # 统计信息
        self.stats: dict[str, int] = {key: 0 for key in keys}
        self._cooldown_until: dict[str, float] = {key: 0.0 for key in keys}
        self._failure_counts: dict[str, int] = {key: 0 for key in keys}
        self._last_error_kind: dict[str, str | None] = {key: None for key in keys}
        self._health_lock = threading.Lock()

        logger.info(
            f"Initialized global API key pool for '{model_name}': "
            f"{len(keys)} keys, max {max_concurrent_per_key} concurrent per key"
        )

    def _get_loop_semaphores(self) -> dict[str, asyncio.Semaphore]:
        """Get (or create) semaphores bound to the current running event loop."""
        loop = asyncio.get_running_loop()
        with self._semaphore_lock:
            semaphores = self._loop_semaphores.get(loop)
            if semaphores is None:
                semaphores = {
                    key: asyncio.Semaphore(self.max_concurrent_per_key)
                    for key in self.keys
                }
                self._loop_semaphores[loop] = semaphores
        return semaphores

    @classmethod
    def get_or_create_pool(
        cls,
        model_name: str,
        keys: list[str],
        max_concurrent_per_key: int = DEFAULT_MAX_CONCURRENT_PER_KEY,
    ) -> "GlobalAPIKeyPool":
        """
        获取或创建全局 Key 池（单例模式）。

        Args:
            model_name: 模型名称
            keys: API key 列表
            max_concurrent_per_key: 每个 key 的最大并发数

        Returns:
            GlobalAPIKeyPool 实例
        """
        with cls._lock:
            # 规范化模型名称（移除空格）
            normalized_name = model_name.strip()

            # 如果已存在，按配置复用或重建
            if normalized_name in cls._pools:
                existing = cls._pools[normalized_name]
                if existing.max_concurrent_per_key == max_concurrent_per_key and existing.keys == keys:
                    return existing

                logger.info(
                    "Reconfiguring global API key pool for %s: per-key concurrency %s -> %s",
                    normalized_name,
                    existing.max_concurrent_per_key,
                    max_concurrent_per_key,
                )
                pool = cls(normalized_name, keys, max_concurrent_per_key)
                cls._pools[normalized_name] = pool
                return pool

            # 创建新的池
            pool = cls(normalized_name, keys, max_concurrent_per_key)
            cls._pools[normalized_name] = pool
            return pool

    @classmethod
    def clear_pools(cls) -> None:
        """清除所有全局 Key 池（主要用于测试）"""
        with cls._lock:
            cls._pools.clear()

    def _eligible_keys(self, excluded_keys: set[str] | None = None) -> list[str]:
        excluded = excluded_keys or set()
        now = time.monotonic()
        with self._health_lock:
            return [
                key
                for key in self.keys
                if key not in excluded and self._cooldown_until.get(key, 0.0) <= now
            ]

    async def acquire_key(self, *, excluded_keys: set[str] | None = None) -> str | None:
        """
        获取一个可用的 API key（阻塞等待）。

        使用轮询策略，自动负载均衡到所有 keys。

        Returns:
            可用的 API key
        """
        # 使用当前 loop 对应的信号量，避免跨 loop 绑定错误
        loop_semaphores = self._get_loop_semaphores()

        # 简单的轮询策略：找到第一个未满的 key
        while True:
            eligible_keys = self._eligible_keys(excluded_keys)
            if not eligible_keys:
                return None

            # 尝试所有的 keys
            for i in range(len(self.keys)):
                with self.index_lock:
                    idx = (self.current_index + i) % len(self.keys)
                    key = self.keys[idx]

                if key not in eligible_keys:
                    continue

                sem = loop_semaphores[key]

                # 尝试获取信号量（使用 try-acquire 模式，避免竞态条件）
                try:
                    # 尝试获取，如果立即失败则继续下一个 key
                    await asyncio.wait_for(sem.acquire(), timeout=0.001)
                    # 成功获取

                    # 更新统计
                    with self.index_lock:
                        self.stats[key] += 1
                        # 移动到下一个 key（下次使用）
                        self.current_index = (idx + 1) % len(self.keys)

                    logger.debug(
                        f"Acquired API key {self.keys.index(key) + 1}/{len(self.keys)} "
                        f"(active: {self.stats[key]})"
                    )
                    return key
                except asyncio.TimeoutError:
                    # 信号量已满，继续尝试下一个 key
                    continue

            # 所有 keys 都满了，等待一小段时间后重试
            await asyncio.sleep(0.01)

    def mark_key_failed(self, key: str, *, reason: str, cooldown_seconds: float) -> None:
        """Mark a key as unhealthy for a cooldown window."""
        if key not in self.stats:
            return
        cooldown = max(0.0, float(cooldown_seconds))
        with self._health_lock:
            self._failure_counts[key] = self._failure_counts.get(key, 0) + 1
            self._last_error_kind[key] = reason
            if cooldown > 0:
                deadline = time.monotonic() + cooldown
                self._cooldown_until[key] = max(self._cooldown_until.get(key, 0.0), deadline)
        logger.warning(
            "Marked API key %s/%s unhealthy for model '%s' due to %s (cooldown %.1fs)",
            self.keys.index(key) + 1,
            len(self.keys),
            self.model_name,
            reason,
            cooldown,
        )

    def mark_key_success(self, key: str) -> None:
        """Clear transient failure state for a key after a successful call."""
        if key not in self.stats:
            return
        with self._health_lock:
            self._failure_counts[key] = 0
            self._last_error_kind[key] = None
            self._cooldown_until[key] = 0.0

    def release_key(self, key: str) -> None:
        """
        释放 API key。

        Args:
            key: 要释放的 API key
        """
        if key not in self.stats:
            logger.warning(f"Attempting to release unknown key: {key[:8]}...")
            return

        sem_released = False

        # 优先释放当前 loop 绑定的 semaphore
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            with self._semaphore_lock:
                semaphores = self._loop_semaphores.get(loop)
            if semaphores and key in semaphores:
                sem = semaphores[key]
                if sem._value < self.max_concurrent_per_key:
                    sem.release()
                    sem_released = True

        # fallback：无运行 loop 或当前 loop 无 semaphore 时，尽力释放任一 loop 的对应 semaphore
        if not sem_released:
            with self._semaphore_lock:
                for semaphores in list(self._loop_semaphores.values()):
                    sem = semaphores.get(key)
                    if sem and sem._value < self.max_concurrent_per_key:
                        sem.release()
                        sem_released = True
                        break

        if not sem_released:
            logger.debug(f"No matching acquired semaphore found for key release: {key[:8]}...")

        with self.index_lock:
            self.stats[key] = max(0, self.stats[key] - 1)

        logger.debug(
            f"Released API key {self.keys.index(key) + 1}/{len(self.keys)} "
            f"(active: {self.stats[key]})"
        )

    @asynccontextmanager
    async def use_key(self) -> AsyncGenerator[str, None]:
        """
        Context manager：自动获取和释放 key。

        用法:
            async with pool.use_key() as key:
                # 使用 key 调用 API
                result = await call_api(key)
        """
        key = await self.acquire_key()
        if key is None:
            raise RuntimeError(f"No healthy API keys available for model '{self.model_name}'")
        try:
            yield key
        finally:
            self.release_key(key)

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息。

        Returns:
            统计信息字典
        """
        return {
            "model": self.model_name,
            "total_keys": len(self.keys),
            "max_concurrent_per_key": self.max_concurrent_per_key,
            "current_active": {
                f"key_{i+1}": count for i, (key, count) in enumerate(self.stats.items())
            },
            "total_active": sum(self.stats.values()),
        }


class LLMConnectionPool:
    """
    Manages HTTP connection pooling for LLM API requests.

    This class provides connection pooling to reduce the overhead of establishing
    new HTTP connections for each LLM API call. Connections are reused across
    multiple requests, improving performance.

    Note: LiteLLM manages its own HTTP sessions internally, so this pool is
    provided for potential future custom integrations or direct HTTP calls.
    """

    _instance: "LLMConnectionPool" | None = None
    _lock = threading.Lock()

    def __init__(
        self,
        pool_size: int = DEFAULT_POOL_SIZE,
        keepalive_timeout: float = KEEPALIVE_TIMEOUT_SECONDS,
    ):
        """
        Initialize the connection pool.

        Args:
            pool_size: Maximum number of connections to keep in the pool
            keepalive_timeout: Seconds to keep connections alive (default: 5 minutes)
        """
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available, connection pooling disabled")
            self.connector = None
            self.session = None
            return

        self.connector = aiohttp.TCPConnector(
            limit=pool_size,
            limit_per_host=pool_size,
            keepalive_timeout=keepalive_timeout,
            enable_cleanup_closed=True,
            force_close=False,
        )
        self.session: aiohttp.ClientSession | None = None
        self._pool_size = pool_size
        self._keepalive_timeout = keepalive_timeout
        logger.info(
            f"LLM connection pool initialized: size={pool_size}, "
            f"keepalive={keepalive_timeout}s"
        )

    @classmethod
    def get_instance(
        cls,
        pool_size: int = DEFAULT_POOL_SIZE,
        keepalive_timeout: float = KEEPALIVE_TIMEOUT_SECONDS,
    ) -> "LLMConnectionPool":
        """
        Get the singleton instance of the connection pool.

        Args:
            pool_size: Maximum number of connections (only used on first call)
            keepalive_timeout: Keep-alive timeout in seconds (only used on first call)

        Returns:
            The singleton LLMConnectionPool instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(pool_size, keepalive_timeout)
        return cls._instance

    async def get_session(self) -> aiohttp.ClientSession | None:
        """
        Get or create the aiohttp session.

        Returns:
            ClientSession if aiohttp is available, None otherwise
        """
        if not AIOHTTP_AVAILABLE or self.connector is None:
            return None

        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=LLM_HTTP_CLIENT_TIMEOUT)
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout,
            )
        return self.session

    async def close(self) -> None:
        """Close the connection pool and release resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        if self.connector:
            await self.connector.close()
        logger.info("LLM connection pool closed")

    @property
    def is_available(self) -> bool:
        """Check if connection pooling is available."""
        return AIOHTTP_AVAILABLE and self.connector is not None
