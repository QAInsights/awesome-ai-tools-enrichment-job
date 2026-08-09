import os
from typing import Optional

from providers.base import ToolInfoProvider


def _get_exa_provider(**kwargs) -> ToolInfoProvider:
    from providers.exa import ExaProvider
    return ExaProvider(**kwargs)


def _get_gemini_provider(**kwargs) -> ToolInfoProvider:
    from providers.gemini import GeminiProvider
    return GeminiProvider(**kwargs)


_PROVIDER_MAP = {
    "exa": _get_exa_provider,
    "gemini": _get_gemini_provider,
}


def get_provider(name: Optional[str] = None, **kwargs) -> ToolInfoProvider:
    """Return a provider instance by name. Defaults to the PROVIDER env var or 'exa'."""
    name = (name or os.getenv("PROVIDER", "exa")).lower()
    if name not in _PROVIDER_MAP:
        raise ValueError(f"Unknown provider: {name}. Available: {list(_PROVIDER_MAP)}")
    return _PROVIDER_MAP[name](**kwargs)
