#!/usr/bin/env python3

"""
API module for Jarvis smart CV pipeline.

This module provides the main API structure and routing.
"""

from .v1 import api_v1_router

__all__ = ['api_v1_router']
