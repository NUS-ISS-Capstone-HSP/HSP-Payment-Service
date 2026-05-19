from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from hsp_payment_service.infrastructure.db import Base


class EchoRecordORM(Base):
    __tablename__ = "echo_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class PaymentORM(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, unique=True)
    amount: Mapped[float] = mapped_column(Float(), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False, default="WECHAT")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class WorkerIncomeORM(Base):
    __tablename__ = "worker_incomes"

    income_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    worker_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    order_amount: Mapped[float] = mapped_column(Float(), nullable=False)
    commission_rate: Mapped[float] = mapped_column(Float(), nullable=False, default=0.7)
    worker_amount: Mapped[float] = mapped_column(Float(), nullable=False)
    settled: Mapped[str] = mapped_column(String(1), nullable=False, default="N")
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
