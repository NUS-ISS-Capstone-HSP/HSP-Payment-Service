from datetime import UTC, datetime
from uuid import uuid4

from hsp_payment_service.domain.models import (
    EchoRecord,
    Payment,
    SourceType,
    WorkerIncome,
)
from hsp_payment_service.repository.interfaces import (
    EchoRepository,
    PaymentRepository,
    WorkerIncomeRepository,
)


class InMemoryEchoRepository(EchoRepository):
    def __init__(self) -> None:
        self._store: dict[str, EchoRecord] = {}

    async def create(self, message: str, source: SourceType) -> EchoRecord:
        record = EchoRecord(
            id=str(uuid4()),
            message=message,
            source=source,
            created_at=datetime.now(UTC),
        )
        self._store[record.id] = record
        return record

    async def get_by_id(self, record_id: str) -> EchoRecord | None:
        return self._store.get(record_id)


class InMemoryPaymentRepository(PaymentRepository):
    def __init__(self) -> None:
        self._store: dict[str, Payment] = {}

    async def create(self, payment: Payment) -> Payment:
        self._store[payment.payment_id] = payment
        return payment

    async def get_by_order_id(self, order_id: str) -> Payment | None:
        for p in self._store.values():
            if p.order_id == order_id:
                return p
        return None

    async def get_by_payment_id(self, payment_id: str) -> Payment | None:
        return self._store.get(payment_id)

    async def update(self, payment: Payment) -> Payment:
        self._store[payment.payment_id] = payment
        return payment

    async def get_summary(
        self, start_date: str, end_date: str
    ) -> tuple[float, float, float, int, int]:
        payments = list(self._store.values())
        total_revenue = 0.0
        total_worker_payout = 0.0
        total_orders = len(payments)
        paid_orders = 0
        for p in payments:
            if p.status.value == "COMPLETED":
                total_revenue += p.amount
                paid_orders += 1
        net_income = total_revenue - total_worker_payout
        return total_revenue, total_worker_payout, net_income, total_orders, paid_orders


class InMemoryWorkerIncomeRepository(WorkerIncomeRepository):
    def __init__(self) -> None:
        self._store: dict[str, WorkerIncome] = {}

    async def create(self, income: WorkerIncome) -> WorkerIncome:
        self._store[income.income_id] = income
        return income

    async def list_by_date_range(
        self, start_date: str, end_date: str
    ) -> list[WorkerIncome]:
        return list(self._store.values())
