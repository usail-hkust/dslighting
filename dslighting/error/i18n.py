"""
Internationalization (i18n) support for DSLighting error messages.

This module provides translation dictionaries and utilities for error messages
and suggestions in multiple languages (currently English and Chinese).

Public API:
    - get_error_message(): Get translated error message by code
    - get_error_suggestion(): Get translated suggestion by code
    - set_error_language(): Set current language for error messages
    - get_error_language(): Get current error language setting
    - SUPPORTED_ERROR_LANGUAGES: List of supported language codes
    - DEFAULT_ERROR_LANGUAGE: Default language code ('en')
    - ERROR_MESSAGE_TEMPLATES: Translation dictionary for error messages
    - ERROR_SUGGESTION_TEMPLATES: Translation dictionary for suggestions
    - get_all_error_codes(): Get list of all error codes
"""

from typing import Dict, Optional
import threading

# Supported languages for error messages
SUPPORTED_ERROR_LANGUAGES = ['en', 'zh']

# Default language for error messages
DEFAULT_ERROR_LANGUAGE = 'en'

# Thread-local storage for error language (thread-safe)
_thread_local = threading.local()

def _get_current_error_language() -> str:
    """Get the thread-local error language setting."""
    return getattr(_thread_local, 'error_language', DEFAULT_ERROR_LANGUAGE)

def _set_current_error_language(lang: str) -> None:
    """Set the thread-local error language setting."""
    _thread_local.error_language = lang


# Legacy global state (kept for backward compatibility, now uses thread-local internally)
_current_error_language: str = DEFAULT_ERROR_LANGUAGE


# =============================================================================
# Error Message Translation Dictionary
# =============================================================================

ERROR_MESSAGE_TEMPLATES = {
    # Configuration Errors (CFG-XXX)
    "CFG-001": {
        "en": "Invalid model configuration: model '{model}' is not supported for provider '{provider}'.",
        "zh": "无效的模型配置：模型 '{model}' 不支持供应商 '{provider}'。",
    },
    "CFG-002": {
        "en": "Missing required configuration key: '{key}' in config file.",
        "zh": "配置文件缺少必需的键：'{key}'。",
    },
    "CFG-003": {
        "en": "Configuration validation failed for field '{field}': {reason}.",
        "zh": "字段 '{field}' 的配置验证失败：{reason}。",
    },
    "CFG-004": {
        "en": "API key not found for provider '{provider}'. Please set the environment variable '{env_var}'.",
        "zh": "未找到供应商 '{provider}' 的 API 密钥。请设置环境变量 '{env_var}'。",
    },
    # Workflow Errors (WRK-XXX)
    "WRK-001": {
        "en": "Workflow '{workflow_name}' failed at step '{step}': {reason}",
        "zh": "工作流 '{workflow_name}' 在步骤 '{step}' 失败：{reason}",
    },
    "WRK-002": {
        "en": "Invalid workflow configuration: circular dependency detected in steps {steps}.",
        "zh": "无效的工作流配置：在步骤 {steps} 中检测到循环依赖。",
    },
    "WRK-003": {
        "en": "Workflow execution timeout after {timeout} seconds.",
        "zh": "工作流执行在 {timeout} 秒后超时。",
    },
    # LLM Service Errors (LLM-XXX)
    "LLM-001": {
        "en": "LLM API request failed: {reason}. Provider: {provider}, Model: {model}.",
        "zh": "LLM API 请求失败：{reason}。供应商：{provider}，模型：{model}。",
    },
    "LLM-002": {
        "en": "LLM rate limit exceeded. Retry after {retry_after} seconds.",
        "zh": "超出 LLM 速率限制。请在 {retry_after} 秒后重试。",
    },
    "LLM-003": {
        "en": "Invalid response from LLM: {reason}.",
        "zh": "LLM 返回无效响应：{reason}。",
    },
    # Data Errors (DAT-XXX)
    "DAT-001": {
        "en": "Failed to load dataset '{dataset}': {reason}.",
        "zh": "加载数据集 '{dataset}' 失败：{reason}。",
    },
    "DAT-002": {
        "en": "Data validation failed: column '{column}' has {invalid_count} invalid values.",
        "zh": "数据验证失败：列 '{column}' 有 {invalid_count} 个无效值。",
    },
    "DAT-003": {
        "en": "Memory error while processing data. Dataset size: {size_mb} MB.",
        "zh": "处理数据时发生内存错误。数据集大小：{size_mb} MB。",
    },
    # Benchmark Errors (BMK-XXX)
    "BMK-001": {
        "en": "Benchmark task '{task_name}' not found.",
        "zh": "未找到基准任务 '{task_name}'。",
    },
    "BMK-002": {
        "en": "Benchmark submission validation failed: {reason}.",
        "zh": "基准提交验证失败：{reason}。",
    },
    # Workspace Errors (WSP-XXX)
    "WSP-001": {
        "en": "Workspace path '{path}' is not writable.",
        "zh": "工作区路径 '{path}' 不可写。",
    },
    "WSP-002": {
        "en": "Failed to create workspace: {reason}.",
        "zh": "创建工作区失败：{reason}。",
    },
    # Task Errors (TSK-XXX)
    "TSK-001": {
        "en": "Task configuration error: {reason}.",
        "zh": "任务配置错误：{reason}。",
    },
    "TSK-002": {
        "en": "Task execution failed: {reason}.",
        "zh": "任务执行失败：{reason}。",
    },
    # General Errors (DSL-XXX)
    "DSL-000": {
        "en": "An unspecified error occurred: {reason}.",
        "zh": "发生未指定的错误：{reason}。",
    },
}


# =============================================================================
# Suggestion Translation Dictionary
# =============================================================================

ERROR_SUGGESTION_TEMPLATES = {
    "CFG-001": {
        "en": "Check the model name against the supported providers list. "
              "Visit https://docs.dslighting.io/providers for available models.",
        "zh": "检查模型名称是否在支持的供应商列表中。 "
              "请访问 https://docs.dslighting.io/providers 获取可用模型列表。",
    },
    "CFG-002": {
        "en": "Add the required key to your config file. "
              "See https://docs.dslighting.io/configuration#required-fields for reference.",
        "zh": "在配置文件中添加必需的键。 "
              "请参考 https://docs.dslighting.io/configuration#required-fields。",
    },
    "CFG-003": {
        "en": "Review the configuration value and ensure it matches the expected format. "
              "Check the documentation for field-specific requirements.",
        "zh": "检查配置值是否匹配预期格式。 "
              "查看文档了解字段特定要求。",
    },
    "CFG-004": {
        "en": "Set the required API key in your environment. "
              "For security, use environment variables rather than hardcoding keys.",
        "zh": "在环境中设置必需的 API 密钥。 "
              "出于安全考虑，请使用环境变量而非硬编码密钥。",
    },
    "WRK-001": {
        "en": "Check the workflow configuration and ensure all steps are properly defined. "
              "Review the step logs for more details.",
        "zh": "检查工作流配置并确保所有步骤正确定义。 "
              "查看步骤日志了解更多详情。",
    },
    "WRK-002": {
        "en": "Remove the circular dependency by restructuring your workflow steps. "
              "Workflows must be a Directed Acyclic Graph (DAG).",
        "zh": "通过重构工作流步骤来移除循环依赖。 "
              "工作流必须是有向无环图（DAG）。",
    },
    "WRK-003": {
        "en": "Consider increasing the timeout value or breaking the workflow into smaller steps. "
              "Optimize slow steps if possible.",
        "zh": "考虑增加超时值或将工作流拆分为更小的步骤。 "
              "如有可能，优化慢速步骤。",
    },
    "LLM-001": {
        "en": "Check your API key and network connection. "
              "The service may be experiencing issues. Try again later.",
        "zh": "检查您的 API 密钥和网络连接。 "
              "服务可能正在经历问题。请稍后重试。",
    },
    "LLM-002": {
        "en": "Implement exponential backoff or reduce request frequency. "
              "Consider upgrading your API plan for higher limits.",
        "zh": "实现指数退避或减少请求频率。 "
              "考虑升级您的 API 计划以获取更高限制。",
    },
    "LLM-003": {
        "en": "The model may have returned malformed output. "
              "Try adjusting the prompt or using a different model.",
        "zh": "模型可能返回了格式错误的输出。 "
              "尝试调整提示词或使用其他模型。",
    },
    "DAT-001": {
        "en": "Verify the file path and format. Ensure the file exists and is readable. "
              "Supported formats: CSV, Parquet, JSON.",
        "zh": "验证文件路径和格式。确保文件存在且可读。 "
              "支持的格式：CSV、Parquet、JSON。",
    },
    "DAT-002": {
        "en": "Clean the data before processing. Consider dropping or imputing invalid values.",
        "zh": "处理前先清洗数据。考虑删除或填充无效值。",
    },
    "DAT-003": {
        "en": "Consider using data sampling, chunked processing, or increasing available memory.",
        "zh": "考虑使用数据采样、分块处理或增加可用内存。",
    },
    "BMK-001": {
        "en": "Verify the task name is correct and exists in the registry. "
              "Use 'dsat benchmark list' to see available tasks.",
        "zh": "验证任务名称是否正确且存在于注册表中。 "
              "使用 'dsat benchmark list' 查看可用任务。",
    },
    "BMK-002": {
        "en": "Ensure your submission matches the expected format. "
              "Check the competition documentation for format requirements.",
        "zh": "确保您的提交符合预期格式。 "
              "查看竞赛文档了解格式要求。",
    },
    "WSP-001": {
        "en": "Check directory permissions and ensure the path exists. "
              "Try creating the directory or using a different path.",
        "zh": "检查目录权限并确保路径存在。 "
              "尝试创建目录或使用其他路径。",
    },
    "WSP-002": {
        "en": "Check available disk space and permissions. "
              "Ensure no conflicting files exist at the target location.",
        "zh": "检查可用磁盘空间和权限。 "
              "确保目标位置没有冲突的文件。",
    },
    "TSK-001": {
        "en": "Review the task configuration for missing or invalid fields. "
              "Check the task documentation for required parameters.",
        "zh": "检查任务配置中缺失或无效的字段。 "
              "查看任务文档了解必需参数。",
    },
    "TSK-002": {
        "en": "Check the task implementation and input data. "
              "Review logs for detailed error information.",
        "zh": "检查任务实现和输入数据。 "
              "查看日志获取详细错误信息。",
    },
    "DSL-000": {
        "en": "Check the logs for more details. If the issue persists, "
              "report it at https://github.com/your-org/dslighting/issues.",
        "zh": "查看日志了解更多详情。如果问题持续，请访问 "
              "https://github.com/your-org/dslighting/issues 报告问题。",
    },
}


def get_error_message(
    error_code: str,
    lang: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Get translated error message template for an error code.

    Args:
        error_code: The error code (e.g., 'CFG-001').
        lang: The language code ('en' or 'zh'). If None, uses current thread-local setting.
        **kwargs: Variables to substitute in the template.

    Returns:
        Translated and formatted message string, or None if not found.
    """
    if lang is None:
        lang = _get_current_error_language()

    # Validate language
    if lang not in SUPPORTED_ERROR_LANGUAGES:
        lang = DEFAULT_ERROR_LANGUAGE

    if error_code not in ERROR_MESSAGE_TEMPLATES:
        return None

    template = ERROR_MESSAGE_TEMPLATES[error_code].get(lang)
    if template is None:
        # Fall back to English if translation not available
        template = ERROR_MESSAGE_TEMPLATES[error_code].get(DEFAULT_ERROR_LANGUAGE)

    if template and kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            # If formatting fails, return unformatted template
            return template

    return template


def get_error_suggestion(
    error_code: str,
    lang: Optional[str] = None,
) -> Optional[str]:
    """Get translated error suggestion for an error code.

    Args:
        error_code: The error code (e.g., 'CFG-001').
        lang: The language code ('en' or 'zh'). If None, uses current thread-local setting.

    Returns:
        Translated suggestion string, or None if not found.
    """
    if lang is None:
        lang = _get_current_error_language()

    # Validate language
    if lang not in SUPPORTED_ERROR_LANGUAGES:
        lang = DEFAULT_ERROR_LANGUAGE

    if error_code not in ERROR_SUGGESTION_TEMPLATES:
        return None

    suggestion = ERROR_SUGGESTION_TEMPLATES[error_code].get(lang)
    if suggestion is None:
        # Fall back to English if translation not available
        suggestion = ERROR_SUGGESTION_TEMPLATES[error_code].get(DEFAULT_ERROR_LANGUAGE)

    return suggestion


def set_error_language(lang: str) -> bool:
    """Set the current language for error messages (thread-local).

    Args:
        lang: The language code ('en' or 'zh').

    Returns:
        True if language was set successfully, False if invalid.
    """
    if lang in SUPPORTED_ERROR_LANGUAGES:
        _set_current_error_language(lang)
        return True
    return False


def get_error_language() -> str:
    """Get the current error message language setting (thread-local).

    Returns:
        The current language code ('en' or 'zh').
    """
    return _get_current_error_language()


def get_all_error_codes() -> list:
    """Get list of all error codes with translations.

    Returns:
        List of error code strings.
    """
    return list(ERROR_MESSAGE_TEMPLATES.keys())


# =============================================================================
# Public API Exports
# =============================================================================

__all__ = [
    # Internationalization functions
    "get_error_message",
    "get_error_suggestion",
    "set_error_language",
    "get_error_language",
    "get_all_error_codes",
    # Constants
    "SUPPORTED_ERROR_LANGUAGES",
    "DEFAULT_ERROR_LANGUAGE",
    # Translation dictionaries (for advanced use cases)
    "ERROR_MESSAGE_TEMPLATES",
    "ERROR_SUGGESTION_TEMPLATES",
]
