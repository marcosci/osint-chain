"""
Registry for storing large map HTML strings to avoid passing them through the LLM context.
"""
import uuid
from typing import Dict, Optional

class MapRegistry:
    _maps: Dict[str, str] = {}
    
    @classmethod
    def register_map(cls, html_content: str) -> str:
        """Register a map HTML content and return its ID."""
        map_id = str(uuid.uuid4())
        cls._maps[map_id] = html_content
        return map_id
    
    @classmethod
    def get_map(cls, map_id: str) -> Optional[str]:
        """Retrieve a map by its ID."""
        return cls._maps.get(map_id)
    
    @classmethod
    def clear(cls):
        """Clear all registered maps."""
        cls._maps.clear()
