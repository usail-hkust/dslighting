"""
Internationalization (i18n) support for DSLighting.

This module provides language configuration and translation utilities
for supporting both English and Chinese UI text.
"""

from __future__ import annotations

from typing import Dict, Optional


# Supported languages
SUPPORTED_LANGUAGES = ['en', 'zh']

# Default language
DEFAULT_LANGUAGE = 'en'

# Current language setting (global state)
_current_language: str = DEFAULT_LANGUAGE

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'en': {
        # Task and system metrics
        'task_progress': 'Task Progress',
        'active_tasks': 'Active Tasks',
        'queue_length': 'Queue Length',
        'cpu_usage': 'CPU Usage',
        'memory_usage': 'Memory Usage',
        'cache_hit': 'Cache Hit',
        'error_rate': 'Error Rate',
        'throughput': 'Throughput',
        'queue_wait': 'Queue Wait',
        'concurrency_utilization': 'Concurrency Utilization',
        'cache_entries': 'Cache Entries',
        'cache_size': 'Cache Size',
        'llm_cost': 'LLM Cost',

        # Experiment name (was run_mode)
        'exp_name': 'Experiment',
        'run_mode': 'Experiment',  # Legacy compatibility

        # Status
        'status': 'Status',
        'running': 'Running',
        'completed': 'Completed',
        'pending': 'Pending',
        'failed': 'Failed',

        # General
        'total': 'Total',
        'percent': '%',
        'seconds': 's',
        'tasks': 'tasks',
        'gb': 'GB',
        'mb': 'MB',
    },
    'zh': {
        # Task and system metrics
        'task_progress': '任务进度',
        'active_tasks': '活跃任务数',
        'queue_length': '队列长度',
        'cpu_usage': 'CPU 利用率',
        'memory_usage': '内存利用率',
        'cache_hit': '缓存命中',
        'error_rate': '错误率',
        'throughput': '吞吐量',
        'queue_wait': '队列等待',
        'concurrency_utilization': '并发利用率',
        'cache_entries': '缓存条目数',
        'cache_size': '缓存大小',
        'llm_cost': 'LLM 成本',

        # Experiment name (was run_mode)
        'exp_name': '实验名称',
        'run_mode': '实验名称',  # Legacy compatibility

        # Status
        'status': '状态',
        'running': '运行中',
        'completed': '已完成',
        'pending': '等待中',
        'failed': '失败',

        # General
        'total': '总计',
        'percent': '%',
        'seconds': '秒',
        'tasks': '任务',
        'gb': 'GB',
        'mb': 'MB',
    },
}


def get_text(key: str, lang: Optional[str] = None) -> str:
    """
    Get translated text for a given key.

    Args:
        key: The translation key (e.g., 'task_progress', 'cpu_usage')
        lang: The language code ('en' or 'zh'). If None, uses current language.

    Returns:
        The translated text string.
    """
    if lang is None:
        lang = _current_language

    # Validate language
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    translations = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])

    # Return translation or key if not found
    return translations.get(key, key)


def set_language(lang: str) -> bool:
    """
    Set the current language.

    Args:
        lang: The language code ('en' or 'zh')

    Returns:
        True if language was set successfully, False if invalid language.
    """
    global _current_language

    if lang in SUPPORTED_LANGUAGES:
        _current_language = lang
        return True
    return False


def get_language() -> str:
    """
    Get the current language setting.

    Returns:
        The current language code ('en' or 'zh').
    """
    return _current_language


def get_supported_languages() -> list:
    """
    Get list of supported language codes.

    Returns:
        List of supported language codes.
    """
    return SUPPORTED_LANGUAGES.copy()
