from abc import ABC, abstractmethod
from typing import Any, Dict


class ToolInfoProvider(ABC):
    """Adapter interface for tool profile generation providers."""

    @abstractmethod
    def get_tool_profile(
        self, company_name: str, tool_name: str, slug: str, url: str = "", category: str = ""
    ) -> Dict[str, Any]:
        """Return a dictionary representing the enriched tool profile."""
        ...
