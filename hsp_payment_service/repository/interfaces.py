from typing import Protocol

from hsp_payment_service.domain.models import (
    EchoRecord,
    Payment,
    PaymentMethod,
    SourceType,
    WorkerIncome,
)


class EchoRepository(Protocol):
    async def create(self, message: str, source: SourceType) -> EchoRecord:
        ...

    async def get_by_id(self, record_id: str) -> EchoRecord | None:
        ...


class PaymentRepository(Protocol):
    async def create(self, payment: Payment) -> Payment:
        ...

    async def get_by_order_id(self, order_id: str) -> Payment | None:
        ...

    async def get_by_payment_id(self, payment_id: str) -> Payment | None:
        ...

    async def update(self, payment: Payment) -> Payment:
        ...

    async def get_summary(
        self, start_date: str, end_date: str
    ) -> tuple[float, float, float, int, int]:
        ...


class WorkerIncomeRepository(Protocol):
    async def create(self, income: WorkerIncome) -> WorkerIncome:
        ...

    async def list_by_date_range(
        self, start_date: str, end_date: str
    ) -> list[WorkerIncome]:
        ...
