import os
import json
import logging
from pathlib import Path
from .llm_service_custom import CustomLLMService
from dsat.config import LLMConfig
from ..core.config import BASE_DIR

logger = logging.getLogger(__name__)

async def get_llm():
    # Reload env to get latest keys/configs
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env", override=True)
    
    # 1. Start with solid defaults from environment
    # Use .strip() and or-fallback to ensure we never have an empty string
    model = (os.getenv("LLM_MODEL") or "").strip() or "openai/deepseek-ai/DeepSeek-V3.1-Terminus"
    api_key = (os.getenv("API_KEY") or "").strip()
    api_base = (os.getenv("API_BASE") or "").strip() or "https://api.openai.com/v1"
    provider = (os.getenv("LLM_PROVIDER") or "").strip() or "openai"
    
    configs_raw = os.getenv("LLM_MODEL_CONFIGS")
    if configs_raw:
        try:
            configs = json.loads(configs_raw)
            if configs and isinstance(configs, dict):
                # Use the first model in the config as the active one
                model_name = list(configs.keys())[0]
                model_cfg = configs[model_name]
                
                model = model_name
                logger.info(f"Loaded active model from CONFIGS: {model}")
                
                # Only overwrite if values are present and not empty
                k = model_cfg.get("api_key")
                if k:
                    if isinstance(k, list) and len(k) > 0:
                        api_key = k[0]
                    elif isinstance(k, str) and k.strip():
                        api_key = k.strip()
                
                if model_cfg.get("api_base") and model_cfg["api_base"].strip():
                    api_base = model_cfg["api_base"].strip()
                
                # Auto-detect provider if not explicitly set
                if model_cfg.get("provider"):
                    provider = model_cfg["provider"]
                else:
                    low_m = model.lower()
                    if "gemini" in low_m or "google" in low_m:
                        provider = "gemini"
                    elif "anthropic" in low_m or "claude" in low_m:
                        provider = "anthropic"
                    else:
                        provider = "openai"
        except Exception as e:
            logger.error(f"FATAL: LLM_MODEL_CONFIGS JSON error in .env: {e}")
            logger.info(f"Falling back to LLM_MODEL environment variable: {model}")

    # Final validation to prevent empty model/key
    if not model or not model.strip():
        model = "openai/deepseek-ai/DeepSeek-V3.1-Terminus"
        
    if not api_key:
        logger.error(f"CRITICAL: API_KEY is missing for model {model}. Check your .env file.")
    else:
        safe_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
        logger.info(f"LLM Final Config: Model={model}, Provider={provider}, Base={api_base}, Key={safe_key}")
        
    config = LLMConfig(
        model=model,
        api_key=api_key,
        api_base=api_base,
        provider=provider,
        temperature=0.2
    )
    return CustomLLMService(config)