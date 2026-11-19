CUSTOMER = "customer"
SUPER_ADMIN = "super_admin"
CLIENT_ADMIN = "client_admin"
CLIENT_SUB_ADMIN = "client_sub_admin"

ADMIN_ROLES = {SUPER_ADMIN, CLIENT_ADMIN, CLIENT_SUB_ADMIN}

TIER_SILVER = "silver"
TIER_GOLD = "gold"
TIER_PLATINUM = "platinum"


def is_admin_role(role: str) -> bool:
    return role in ADMIN_ROLES
