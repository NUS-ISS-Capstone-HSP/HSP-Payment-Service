from pathlib import Path

import pytest

from hsp_payment_service.domain.models import (
    Payment,
    PaymentMethod,
    PaymentStatus,
    SourceType,
    WorkerIncome,
)
from hsp_payment_service.infrastructure.db import (
    create_engine,
    create_session_factory,
    init_db,
)
from hsp_payment_service.repository.mysql import (
    SQLAlchemyEchoRepository,
    SQLAlchemyPaymentRepository,
    SQLAlchemyWorkerIncomeRepository,
)


@pytest.mark.asyncio
async def test_sqlalchemy_repository_create_and_get(tmp_path: Path) -> None:
    db_file = tmp_path / "echo.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyEchoRepository(create_session_factory(engine))

    created = await repository.create("repo-message", SourceType.GRPC)
    fetched = await repository.get_by_id(created.id)

    assert created.message == "repo-message"
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.source == SourceType.GRPC

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_repository_get_missing_returns_none(tmp_path: Path) -> None:
    db_file = tmp_path / "echo.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyEchoRepository(create_session_factory(engine))

    fetched = await repository.get_by_id("missing-id")
    assert fetched is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_payment_repository_create_get_update_and_summary(
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "payment.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyPaymentRepository(create_session_factory(engine))
    payment = Payment(
        payment_id="payment-1",
        order_id="order-1",
        amount=120.0,
        method=PaymentMethod.CASH,
    )

    created = await repository.create(payment)
    by_order = await repository.get_by_order_id("order-1")
    by_payment_id = await repository.get_by_payment_id("payment-1")

    created.status = PaymentStatus.COMPLETED
    updated = await repository.update(created)
    summary = await repository.get_summary("", "")

    assert created.method == PaymentMethod.CASH
    assert by_order is not None
    assert by_order.payment_id == "payment-1"
    assert by_payment_id is not None
    assert by_payment_id.order_id == "order-1"
    assert updated.status == PaymentStatus.COMPLETED
    assert summary == (120.0, 0.0, 120.0, 1, 1)

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_payment_repository_missing_payment_returns_none(
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "payment.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyPaymentRepository(create_session_factory(engine))

    assert await repository.get_by_order_id("missing-order") is None
    assert await repository.get_by_payment_id("missing-payment") is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_worker_income_repository_create_and_list(
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "income.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyWorkerIncomeRepository(create_session_factory(engine))
    income = WorkerIncome(
        income_id="income-1",
        order_id="order-1",
        worker_id="worker-1",
        order_amount=200.0,
        worker_amount=140.0,
    )

    created = await repository.create(income)
    incomes = await repository.list_by_date_range("", "")

    assert created.income_id == "income-1"
    assert created.worker_amount == 140.0
    assert len(incomes) == 1
    assert incomes[0].income_id == "income-1"

    await engine.dispose()
