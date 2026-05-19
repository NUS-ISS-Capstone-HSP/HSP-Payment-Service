import pytest

from hsp_payment_service.domain.errors import DuplicateError, NotFoundError, ValidationError
from hsp_payment_service.domain.models import PaymentMethod, PaymentStatus
from hsp_payment_service.repository.in_memory import (
    InMemoryPaymentRepository,
    InMemoryWorkerIncomeRepository,
)
from hsp_payment_service.service.payment_service import PaymentService


def build_service() -> PaymentService:
    return PaymentService(
        InMemoryPaymentRepository(), InMemoryWorkerIncomeRepository()
    )


@pytest.mark.asyncio
async def test_create_payment_success() -> None:
    svc = build_service()
    payment = await svc.create_payment("order-001", 299.0, PaymentMethod.WECHAT)

    assert payment.payment_id
    assert payment.order_id == "order-001"
    assert payment.amount == 299.0
    assert payment.method == PaymentMethod.WECHAT
    assert payment.status == PaymentStatus.PENDING


@pytest.mark.asyncio
async def test_create_payment_duplicate_raises() -> None:
    svc = build_service()
    await svc.create_payment("order-001", 100.0)

    with pytest.raises(DuplicateError):
        await svc.create_payment("order-001", 200.0)


@pytest.mark.asyncio
async def test_create_payment_empty_order_id_raises() -> None:
    svc = build_service()
    with pytest.raises(ValidationError):
        await svc.create_payment("  ", 100.0)


@pytest.mark.asyncio
async def test_create_payment_negative_amount_raises() -> None:
    svc = build_service()
    with pytest.raises(ValidationError):
        await svc.create_payment("order-001", -1.0)


@pytest.mark.asyncio
async def test_get_payment_success() -> None:
    svc = build_service()
    created = await svc.create_payment("order-001", 299.0)
    fetched = await svc.get_payment("order-001")

    assert fetched.payment_id == created.payment_id
    assert fetched.amount == 299.0


@pytest.mark.asyncio
async def test_get_payment_not_found_raises() -> None:
    svc = build_service()
    with pytest.raises(NotFoundError):
        await svc.get_payment("nonexistent")


@pytest.mark.asyncio
async def test_process_payment_callback_success() -> None:
    svc = build_service()
    created = await svc.create_payment("order-001", 299.0)
    result = await svc.process_payment_callback(created.payment_id, True)

    assert result.status == PaymentStatus.COMPLETED
    assert result.paid_at is not None


@pytest.mark.asyncio
async def test_process_payment_callback_failure() -> None:
    svc = build_service()
    created = await svc.create_payment("order-001", 299.0)
    result = await svc.process_payment_callback(created.payment_id, False)

    assert result.status == PaymentStatus.FAILED


@pytest.mark.asyncio
async def test_process_payment_callback_not_found_raises() -> None:
    svc = build_service()
    with pytest.raises(NotFoundError):
        await svc.process_payment_callback("no-such-id", True)


@pytest.mark.asyncio
async def test_calculate_worker_income_success() -> None:
    svc = build_service()
    income = await svc.calculate_worker_income("order-001", "worker-1", 200.0)

    assert income.income_id
    assert income.order_id == "order-001"
    assert income.worker_id == "worker-1"
    assert income.order_amount == 200.0
    assert income.commission_rate == 0.7
    assert income.worker_amount == 140.0
    assert income.settled == "N"


@pytest.mark.asyncio
async def test_calculate_worker_income_validation_raises() -> None:
    svc = build_service()
    with pytest.raises(ValidationError):
        await svc.calculate_worker_income("", "worker-1", 100.0)


@pytest.mark.asyncio
async def test_get_revenue_summary() -> None:
    svc = build_service()
    await svc.create_payment("order-001", 100.0)
    created = await svc.create_payment("order-002", 200.0)
    await svc.process_payment_callback(created.payment_id, True)
    await svc.calculate_worker_income("order-002", "worker-1", 200.0)

    total_rev, total_payout, net, orders, paid, incomes = (
        await svc.get_revenue_summary("", "")
    )

    assert orders == 2
    assert paid == 1
    assert total_rev == 200.0
    assert len(incomes) == 1
    assert total_payout == 140.0
    assert net == 60.0
