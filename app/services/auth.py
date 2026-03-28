import datetime
import hashlib
import secrets
import uuid

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.user import Group, GroupPermission, Session, User, UserGroup


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(db: AsyncSession, user_id: uuid.UUID) -> str:
    token = secrets.token_urlsafe(32)
    session = Session(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=settings.session_max_age),
    )
    db.add(session)
    await db.commit()
    return token


async def get_user_by_session_token(db: AsyncSession, token: str) -> User | None:
    token_hash = hash_token(token)
    result = await db.execute(
        select(Session)
        .where(Session.token_hash == token_hash, Session.expires_at > datetime.datetime.now(datetime.UTC))
        .options(
            selectinload(Session.user)
            .selectinload(User.user_groups)
            .selectinload(UserGroup.group)
            .selectinload(Group.group_permissions)
            .selectinload(GroupPermission.permission)
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    return session.user


async def delete_session(db: AsyncSession, token: str) -> None:
    token_hash = hash_token(token)
    result = await db.execute(select(Session).where(Session.token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        await db.commit()
