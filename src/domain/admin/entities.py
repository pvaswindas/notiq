from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class Admin:
    id: str
    name: str
    email: str
    password_hash: str
    is_active: bool
    created_at: datetime


@dataclass(slots=True, frozen=True)
class Role:
    id: str
    name: str
    created_at: datetime


@dataclass(slots=True, frozen=True)
class Permission:
    id: str
    name: str
    created_at: datetime
