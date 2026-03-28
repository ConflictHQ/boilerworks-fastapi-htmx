import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDType


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    user_groups: Mapped[list["UserGroup"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def groups(self) -> list["Group"]:
        return [ug.group for ug in self.user_groups]

    @property
    def permissions(self) -> set[str]:
        perms: set[str] = set()
        for ug in self.user_groups:
            for gp in ug.group.group_permissions:
                perms.add(gp.permission.code)
        return perms


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="sessions")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    group_permissions: Mapped[list["GroupPermission"]] = relationship(back_populates="permission")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    group_permissions: Mapped[list["GroupPermission"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    user_groups: Mapped[list["UserGroup"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_groups")
    group: Mapped["Group"] = relationship(back_populates="user_groups")


class GroupPermission(Base):
    __tablename__ = "group_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )

    group: Mapped["Group"] = relationship(back_populates="group_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="group_permissions")
