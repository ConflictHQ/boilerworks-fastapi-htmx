from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FormDefinition(TimestampMixin, Base):
    __tablename__ = "form_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    submissions: Mapped[list["FormSubmission"]] = relationship(back_populates="form_definition")


class FormSubmission(TimestampMixin, Base):
    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_definition_id: Mapped[int] = mapped_column(
        ForeignKey("form_definitions.id", ondelete="CASCADE"), nullable=False
    )
    submitted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    form_definition: Mapped["FormDefinition"] = relationship(back_populates="submissions")
