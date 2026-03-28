import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDType


class FormDefinition(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "form_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    submissions: Mapped[list["FormSubmission"]] = relationship(back_populates="form_definition")


class FormSubmission(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "form_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    form_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("form_definitions.id", ondelete="CASCADE"), nullable=False
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    form_definition: Mapped["FormDefinition"] = relationship(back_populates="submissions")
