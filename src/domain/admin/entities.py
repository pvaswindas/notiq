from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class Admin:
    """Administrative operator identity used by RBAC-enabled control APIs.

    Responsibilities:
    - Represent immutable admin account state loaded from persistence.

    Architectural role:
    - Domain entity consumed by admin use cases and authentication services.
    """

    id: str
    name: str
    email: str
    password_hash: str
    is_active: bool
    created_at: datetime


@dataclass(slots=True, frozen=True)
class Role:
    """Named RBAC role grouping permissions for admin authorization."""

    id: str
    name: str
    created_at: datetime


@dataclass(slots=True, frozen=True)
class Permission:
    """Atomic RBAC permission used to gate privileged admin actions."""

    id: str
    name: str
    created_at: datetime
