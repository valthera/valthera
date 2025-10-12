#!/usr/bin/env python3

"""
Core module for Jarvis smart CV pipeline.

This module provides core functionality including caching, processing pipelines,
and shared utilities.
"""

from .cache import ResultCache, CacheEntry, get_cache, cleanup_cache

__all__ = [
    'ResultCache',
    'CacheEntry', 
    'get_cache',
    'cleanup_cache'
]
