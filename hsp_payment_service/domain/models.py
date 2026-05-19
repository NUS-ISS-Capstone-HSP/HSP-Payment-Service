from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SourceType(StrEnum):
    HTTP = "HTTP"
    GRPC = "GRPC"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(StrEnum):
    WECHAT = "WECHAT"
    CASH = "CASH"


@dataclass(slots=True)
class EchoRecord:
    id: str
    message: str
    source: SourceType
    created_at: datetime


@dataclass(slots=True)
class Payment:
    payment_id: str
    order_id: str
    amount: float
    method: PaymentMethod = PaymentMethod.WECHAT
    status: PaymentStatus = PaymentStatus.PENDING
    paid_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class WorkerIncome:
    income_id: str
    order_id: str
    worker_id: str
    order_amount: float
    commission_rate: float = 0.7
    worker_amount: float = 0.0
    settled: str = "N"
    settled_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
