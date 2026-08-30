from dslighting.config import LLMConfig
from dslighting.services.llm.pool import GlobalAPIKeyPool
from dslighting.services.llm.service import LLMService


def test_completion_kwargs_forward_default_headers() -> None:
    GlobalAPIKeyPool.clear_pools()
    service = LLMService(
        LLMConfig(
            model="custom-model",
            api_key="secret",
            api_base="https://example.com/v1",
            provider="openai",
            default_headers={"x-foo": "true"},
        )
    )

    kwargs = service._build_completion_kwargs(
        messages=[{"role": "user", "content": "hello"}],
        response_format=None,
        api_key="secret",
    )

    assert kwargs["custom_llm_provider"] == "openai"
    assert kwargs["extra_headers"] == {"x-foo": "true"}
