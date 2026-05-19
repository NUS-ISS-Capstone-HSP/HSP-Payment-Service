from datetime import UTC, datetime
from uuid import uuid4

from hsp_payment_service.domain.errors import (
    DuplicateError,
    NotFoundError,
    ValidationError,
)
from hsp_payment_service.domain.models import (
    Payment,
    PaymentMethod,
    PaymentStatus,
    WorkerIncome,
)
from hsp_payment_service.repository.interfaces import (
    PaymentRepository,
    WorkerIncomeRepository,
)

_DEFAULT_COMMISSION_RATE = 0.7


class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        income_repository: WorkerIncomeRepository,
    ) -> None:
        self._payment_repo = payment_repository
        self._income_repo = income_repository

    async def create_payment(
        self,
        order_id: str,
        amount: float,
        method: PaymentMethod = PaymentMethod.WECHAT,
    ) -> Payment:
        if not order_id.strip():
            raise ValidationError("order_id must not be empty")
        if amount <= 0:
            raise ValidationError("amount must be positive")

        existing = await self._payment_repo.get_by_order_id(order_id.strip())
        if existing is not None:
            raise DuplicateError(f"payment for order '{order_id}' already exists")

        payment = Payment(
            payment_id=str(uuid4()),
            order_id=order_id.strip(),
            amount=amount,
            method=method,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self._payment_repo.create(payment)

    async def get_payment(self, order_id: str) -> Payment:
        if not order_id.strip():
            raise ValidationError("order_id must not be empty")
        payment = await self._payment_repo.get_by_order_id(order_id.strip())
        if payment is None:
            raise NotFoundError(f"payment for order '{order_id}' not found")
        return payment

    async def process_payment_callback(
        self, payment_id: str, success: bool
    ) -> Payment:
        if not payment_id.strip():
            raise ValidationError("payment_id must not be empty")

        payment = await self._payment_repo.get_by_payment_id(payment_id.strip())
        if payment is None:
            raise NotFoundError(f"payment '{payment_id}' not found")

        payment.status = (
            PaymentStatus.COMPLETED if success else PaymentStatus.FAILED
        )
        payment.paid_at = datetime.now(UTC) if success else None
        payment.updated_at = datetime.now(UTC)
        return await self._payment_repo.update(payment)

    async def calculate_worker_income(
        self,
        order_id: str,
        worker_id: str,
        order_amount: float,
    ) -> WorkerIncome:
        if not order_id.strip():
            raise ValidationError("order_id must not be empty")
        if not worker_id.strip():
            raise ValidationError("worker_id must not be empty")
        if order_amount <= 0:
            raise ValidationError("order_amount must be positive")

        worker_amount = round(order_amount * _DEFAULT_COMMISSION_RATE, 2)
        income = WorkerIncome(
            income_id=str(uuid4()),
            order_id=order_id.strip(),
            worker_id=worker_id.strip(),
            order_amount=order_amount,
            commission_rate=_DEFAULT_COMMISSION_RATE,
            worker_amount=worker_amount,
            settled="N",
            created_at=datetime.now(UTC),
        )
        return await self._income_repo.create(income)

    async def get_revenue_summary(
        self, start_date: str, end_date: str
    ) -> tuple[float, float, float, int, int, list[WorkerIncome]]:
        total_revenue, total_payout, net, orders, paid = (
            await self._payment_repo.get_summary(start_date, end_date)
        )
        incomes = await self._income_repo.list_by_date_range(start_date, end_date)
        total_payout = sum(i.worker_amount for i in incomes)
        net = total_revenue - total_payout
        return total_revenue, total_payout, net, orders, paid, incomes
