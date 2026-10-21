from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    CEO = "ceo"
    ADMINISTRATOR = "administrator"
    BRANCH_MANAGER = "branch_manager"
    WAREHOUSE_MANAGER = "warehouse_manager"
    SALES_OFFICER = "sales_officer"
    PROCUREMENT_OFFICER = "procurement_officer"
    LOGISTICS_OFFICER = "logistics_officer"
    DISPATCH_RIDER = "dispatch_rider"


CATALOG_READ = "catalog:read"
CATALOG_WRITE = "catalog:write"
INVENTORY_READ = "inventory:read"
INVENTORY_WRITE = "inventory:write"
SALES_READ = "sales:read"
SALES_WRITE = "sales:write"
PROCUREMENT_READ = "procurement:read"
PROCUREMENT_WRITE = "procurement:write"
LOGISTICS_READ = "logistics:read"
LOGISTICS_WRITE = "logistics:write"
REPORTING_READ = "reporting:read"
AUTH_MANAGE = "auth:manage"

ALL_PERMISSIONS = frozenset({
    CATALOG_READ,
    CATALOG_WRITE,
    INVENTORY_READ,
    INVENTORY_WRITE,
    SALES_READ,
    SALES_WRITE,
    PROCUREMENT_READ,
    PROCUREMENT_WRITE,
    LOGISTICS_READ,
    LOGISTICS_WRITE,
    REPORTING_READ,
    AUTH_MANAGE,
})

ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.CEO: ALL_PERMISSIONS,
    Role.ADMINISTRATOR: ALL_PERMISSIONS,
    Role.BRANCH_MANAGER: frozenset({
        CATALOG_READ,
        INVENTORY_READ,
        INVENTORY_WRITE,
        SALES_READ,
        SALES_WRITE,
        REPORTING_READ,
    }),
    Role.WAREHOUSE_MANAGER: frozenset({
        CATALOG_READ,
        INVENTORY_READ,
        INVENTORY_WRITE,
        PROCUREMENT_READ,
        REPORTING_READ,
    }),
    Role.SALES_OFFICER: frozenset({
        CATALOG_READ,
        INVENTORY_READ,
        SALES_READ,
        SALES_WRITE,
    }),
    Role.PROCUREMENT_OFFICER: frozenset({
        CATALOG_READ,
        PROCUREMENT_READ,
        PROCUREMENT_WRITE,
        REPORTING_READ,
    }),
    Role.LOGISTICS_OFFICER: frozenset({
        INVENTORY_READ,
        LOGISTICS_READ,
        LOGISTICS_WRITE,
    }),
    Role.DISPATCH_RIDER: frozenset({LOGISTICS_READ}),
}


@dataclass(frozen=True)
class User:
    user_id: int
    username: str
    email: str
    password_hash: str
    role: Role
    is_active: bool = True

    @property
    def permissions(self) -> frozenset[str]:
        return ROLE_PERMISSIONS[self.role]

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
