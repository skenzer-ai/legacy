"""Advanced caching system for Augment AI Platform."""

# Import basic cache manager from the renamed file
from ..cache_manager import cache_manager, CacheManager

from .strategy import (
    AdvancedCacheManager,
    CacheConfig,
    CacheLevel,
    InvalidationStrategy,
    CachePattern,
    advanced_cache,
    cached,
    cache_context
)

__all__ = [
    # Basic cache manager (for backward compatibility)
    "cache_manager",
    "CacheManager",
    
    # Advanced cache features
    "AdvancedCacheManager",
    "CacheConfig",
    "CacheLevel", 
    "InvalidationStrategy",
    "CachePattern",
    "advanced_cache",
    "cached",
    "cache_context"
]