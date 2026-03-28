from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class WorkflowDefinition(TimestampMixin, Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    states: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    transitions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    instances: Mapped[list["WorkflowInstance"]] = relationship(back_populates="workflow_definition")


class WorkflowInstance(TimestampMixin, Base):
    __tablename__ = "workflow_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_definition_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False
    )
    current_state: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    workflow_definition: Mapped["WorkflowDefinition"] = relationship(back_populates="instances")
    transition_logs: Mapped[list["TransitionLog"]] = relationship(back_populates="workflow_instance")


class TransitionLog(TimestampMixin, Base):
    __tablename__ = "transition_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_instance_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False
    )
    from_state: Mapped[str] = mapped_column(String(100), nullable=False)
    to_state: Mapped[str] = mapped_column(String(100), nullable=False)
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    workflow_instance: Mapped["WorkflowInstance"] = relationship(back_populates="transition_logs")
