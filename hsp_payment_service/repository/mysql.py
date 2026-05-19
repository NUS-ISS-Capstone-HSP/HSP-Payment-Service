from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hsp_payment_service.domain.models import (
    EchoRecord,
    Payment,
    PaymentMethod,
    PaymentStatus,
    SourceType,
    WorkerIncome,
)
from hsp_payment_service.infrastructure.orm import (
    EchoRecordORM,
    PaymentORM,
    WorkerIncomeORM,
)
from hsp_payment_service.repository.interfaces import (
    EchoRepository,
    PaymentRepository,
    WorkerIncomeRepository,
)


class SQLAlchemyEchoRepository(EchoRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, message: str, source: SourceType) -> EchoRecord:
        row = EchoRecordORM(
            id=str(uuid4()),
            message=message,
            source=source.value,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _echo_to_domain(row)

    async def get_by_id(self, record_id: str) -> EchoRecord | None:
        async with self._session_factory() as session:
            stmt = select(EchoRecordORM).where(EchoRecordORM.id == record_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _echo_to_domain(row)


class SQLAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, payment: Payment) -> Payment:
        row = PaymentORM(
            payment_id=payment.payment_id,
            order_id=payment.order_id,
            amount=payment.amount,
            method=payment.method.value,
            status=payment.status.value,
            paid_at=payment.paid_at,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _payment_to_domain(row)

    async def get_by_order_id(self, order_id: str) -> Payment | None:
        async with self._session_factory() as session:
            stmt = select(PaymentORM).where(PaymentORM.order_id == order_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _payment_to_domain(row)

    async def get_by_payment_id(self, payment_id: str) -> Payment | None:
        async with self._session_factory() as session:
            stmt = select(PaymentORM).where(PaymentORM.payment_id == payment_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _payment_to_domain(row)

    async def update(self, payment: Payment) -> Payment:
        async with self._session_factory() as session:
            stmt = select(PaymentORM).where(
                PaymentORM.payment_id == payment.payment_id
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                return await self.create(payment)
            row.status = payment.status.value
            row.paid_at = payment.paid_at
            row.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(row)
        return _payment_to_domain(row)

    async def get_summary(
        self, start_date: str, end_date: str
    ) -> tuple[float, float, float, int, int]:
        async with self._session_factory() as session:
            count_q = select(func.count(PaymentORM.payment_id))
            total_result = await session.execute(count_q)
            total_orders = total_result.scalar() or 0

            paid_q = select(func.count(PaymentORM.payment_id)).where(
                PaymentORM.status == "COMPLETED"
            )
            paid_result = await session.execute(paid_q)
            paid_orders = paid_result.scalar() or 0

            revenue_q = select(func.sum(PaymentORM.amount)).where(
                PaymentORM.status == "COMPLETED"
            )
            rev_result = await session.execute(revenue_q)
            total_revenue = rev_result.scalar() or 0.0

        total_worker_payout = 0.0
        net_income = total_revenue - total_worker_payout
        return total_revenue, total_worker_payout, net_income, total_orders, paid_orders


class SQLAlchemyWorkerIncomeRepository(WorkerIncomeRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, income: WorkerIncome) -> WorkerIncome:
        row = WorkerIncomeORM(
            income_id=income.income_id,
            order_id=income.order_id,
            worker_id=income.worker_id,
            order_amount=income.order_amount,
            commission_rate=income.commission_rate,
            worker_amount=income.worker_amount,
            settled=income.settled,
            settled_at=income.settled_at,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _worker_income_to_domain(row)

    async def list_by_date_range(
        self, start_date: str, end_date: str
    ) -> list[WorkerIncome]:
        async with self._session_factory() as session:
            stmt = select(WorkerIncomeORM).order_by(WorkerIncomeORM.created_at.desc())
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [_worker_income_to_domain(r) for r in rows]


def _echo_to_domain(row: EchoRecordORM) -> EchoRecord:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return EchoRecord(
        id=row.id,
        message=row.message,
        source=SourceType(row.source),
        created_at=created_at,
    )


def _payment_to_domain(row: PaymentORM) -> Payment:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    updated_at = row.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    paid_at = row.paid_at
    if paid_at and paid_at.tzinfo is None:
        paid_at = paid_at.replace(tzinfo=UTC)
    return Payment(
        payment_id=row.payment_id,
        order_id=row.order_id,
        amount=row.amount,
        method=PaymentMethod(row.method),
        status=PaymentStatus(row.status),
        paid_at=paid_at,
        created_at=created_at,
        updated_at=updated_at,
    )


def _worker_income_to_domain(row: WorkerIncomeORM) -> WorkerIncome:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    settled_at = row.settled_at
    if settled_at and settled_at.tzinfo is None:
        settled_at = settled_at.replace(tzinfo=UTC)
    return WorkerIncome(
        income_id=row.income_id,
        order_id=row.order_id,
        worker_id=row.worker_id,
        order_amount=row.order_amount,
        commission_rate=row.commission_rate,
        worker_amount=row.worker_amount,
        settled=row.settled,
        settled_at=settled_at,
        created_at=created_at,
    )
