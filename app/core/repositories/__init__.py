"""
This module contains the repository classes for the application.

Each repository class is responsible for interacting with the database and providing
a clean interface for data access and manipulation.

Following repository classes are defined:
- UserRepository: Handles user-related database operations.
- BaseRepository: Provides a base class for all repository classes.
"""

from app.core.repositories.base_repository import BaseRepository


__all__ = ["BaseRepository"]
