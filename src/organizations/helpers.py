from common.db import manager
from organizations.models import Organization
from users.models import User


async def fetch_organization(organization_id) -> Organization:
    """Fetches the organization with the users.

    This definition allows to break the circular dependency
    between the users and organizations models.
    """
    query = Organization.select().where(Organization.id == organization_id)
    matches = await manager.prefetch(query, User.select())
    matches = list(matches)
    if not matches:
        return None
    organization = matches[0]

    if organization.users:
        organization.users = list(organization.users)

    return organization
