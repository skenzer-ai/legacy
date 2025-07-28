"""
Man-O-Man Service Registry Management System

A comprehensive service registry management platform designed to intelligently
classify, validate, and manage API services for the unified AugmentAgent.
Handles 1,288+ Infraon API operations across 83+ service modules through
intelligent tier classification and procedural validation.
"""

__version__ = "1.0.0"
__author__ = "Augment AI Platform"

from .models import (
    ServiceRegistry,
    ServiceDefinition,
    APISpecification,
    ServiceOperation
)

__all__ = [
    "ServiceRegistry",
    "ServiceDefinition", 
    "APISpecification",
    "ServiceOperation"
]