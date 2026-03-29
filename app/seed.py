"""Seed the database with default permissions, groups, and admin user."""

import asyncio

from sqlalchemy import select

from app.database import async_session_factory, engine
from app.models import Base
from app.models.user import Group, GroupPermission, Permission, User, UserGroup
from app.services.auth import hash_password

PERMISSIONS = [
    "items.view",
    "items.create",
    "items.edit",
    "items.delete",
    "categories.view",
    "categories.create",
    "categories.edit",
    "categories.delete",
    "forms.view",
    "forms.create",
    "forms.edit",
    "forms.delete",
    "forms.submit",
    "workflows.view",
    "workflows.create",
    "workflows.edit",
    "workflows.delete",
]

GROUPS = {
    "admin": PERMISSIONS,
    "editor": [p for p in PERMISSIONS if "delete" not in p],
    "viewer": [p for p in PERMISSIONS if "view" in p],
}


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Create permissions
        perm_map: dict[str, Permission] = {}
        for code in PERMISSIONS:
            result = await db.execute(select(Permission).where(Permission.code == code))
            perm = result.scalar_one_or_none()
            if not perm:
                perm = Permission(code=code, description=code.replace(".", " ").title())
                db.add(perm)
            perm_map[code] = perm
        await db.flush()

        # Create groups with permissions
        for group_name, group_perms in GROUPS.items():
            result = await db.execute(select(Group).where(Group.name == group_name))
            group = result.scalar_one_or_none()
            if not group:
                group = Group(name=group_name, description=f"{group_name.title()} group")
                db.add(group)
                await db.flush()

                for perm_code in group_perms:
                    db.add(GroupPermission(group_id=group.id, permission_id=perm_map[perm_code].id))

        await db.flush()

        # Create admin user
        result = await db.execute(select(User).where(User.email == "admin@boilerworks.dev"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@boilerworks.dev",
                password_hash=hash_password("password"),
                display_name="Admin",
            )
            db.add(admin)
            await db.flush()

            admin_group = (await db.execute(select(Group).where(Group.name == "admin"))).scalar_one()
            db.add(UserGroup(user_id=admin.id, group_id=admin_group.id))

        await db.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
