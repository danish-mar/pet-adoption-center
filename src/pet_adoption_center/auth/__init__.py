"""Authentication package providing hashing and session state."""

from .hasher import hash_password, verify_password
from .session import SessionManager, session

__all__ = ["hash_password", "verify_password", "SessionManager", "session"]
