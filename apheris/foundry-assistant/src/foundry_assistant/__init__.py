"""Support assistant: a decision-model KB router with optional local phrasing."""

from .api import answer, build_backend, load_knowledge_base, load_routing
from .contracts import Reply

__all__ = ["answer", "build_backend", "load_knowledge_base", "load_routing", "Reply"]
