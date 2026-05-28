import grpc
import pytest
import pytest_asyncio

from hsp_payment_service.repository.in_memory import (
    InMemoryPaymentRepository,
    InMemoryWorkerIncomeRepository,
)
from hsp_payment_service.service.payment_service import PaymentService
from hsp_payment_service.transport.grpc.service import PaymentGrpcService
from rpc.payment.v1 import payment_pb2, payment_pb2_grpc


@pytest_asyncio.fixture
async def grpc_stub() -> payment_pb2_grpc.PaymentServiceStub:
    service = PaymentService(
        InMemoryPaymentRepository(), InMemoryWorkerIncomeRepository()
    )

    server = grpc.aio.server()
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentGrpcService(service), server
    )
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()

    channel = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
    stub = payment_pb2_grpc.PaymentServiceStub(channel)

    try:
        yield stub
    finally:
        await channel.close()
        await server.stop(0)


@pytest.mark.asyncio
async def test_payment_grpc_health_success(
    grpc_stub: payment_pb2_grpc.PaymentServiceStub,
) -> None:
    response = await grpc_stub.Health(payment_pb2.HealthRequest())

    assert response.status == "ok"


@pytest.mark.asyncio
async def test_payment_grpc_create_get_callback_income_and_summary_success(
    grpc_stub: payment_pb2_grpc.PaymentServiceStub,
) -> None:
    created = await grpc_stub.CreatePayment(
        payment_pb2.CreatePaymentRequest(
            order_id="order-grpc",
            amount=80.0,
            method=payment_pb2.PAYMENT_METHOD_CASH,
        )
    )
    fetched = await grpc_stub.GetPayment(
        payment_pb2.GetPaymentRequest(order_id="order-grpc")
    )
    callback = await grpc_stub.ProcessPaymentCallback(
        payment_pb2.ProcessPaymentCallbackRequest(
            payment_id=created.payment.payment_id,
            success=True,
        )
    )
    income = await grpc_stub.CalculateWorkerIncome(
        payment_pb2.CalculateWorkerIncomeRequest(
            order_id="order-grpc",
            worker_id="worker-1",
            order_amount=80.0,
        )
    )
    summary = await grpc_stub.GetRevenueSummary(
        payment_pb2.GetRevenueSummaryRequest()
    )

    assert created.payment.method == payment_pb2.PAYMENT_METHOD_CASH
    assert fetched.payment.payment_id == created.payment.payment_id
    assert callback.payment.status == payment_pb2.PAYMENT_STATUS_COMPLETED
    assert income.income.worker_amount == 56.0
    assert summary.summary.total_revenue == 80.0
    assert summary.summary.total_worker_payout == 56.0
    assert summary.summary.net_income == 24.0
    assert summary.summary.paid_orders == 1
    assert len(summary.incomes) == 1


@pytest.mark.asyncio
async def test_payment_grpc_create_duplicate_returns_already_exists(
    grpc_stub: payment_pb2_grpc.PaymentServiceStub,
) -> None:
    request = payment_pb2.CreatePaymentRequest(order_id="dup", amount=100.0)
    await grpc_stub.CreatePayment(request)

    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await grpc_stub.CreatePayment(request)

    assert exc_info.value.code() == grpc.StatusCode.ALREADY_EXISTS


@pytest.mark.asyncio
async def test_payment_grpc_create_invalid_argument(
    grpc_stub: payment_pb2_grpc.PaymentServiceStub,
) -> None:
    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await grpc_stub.CreatePayment(
            payment_pb2.CreatePaymentRequest(order_id="bad", amount=0.0)
        )

    assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.asyncio
async def test_payment_grpc_get_missing_returns_not_found(
    grpc_stub: payment_pb2_grpc.PaymentServiceStub,
) -> None:
    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await grpc_stub.GetPayment(payment_pb2.GetPaymentRequest(order_id="missing"))

    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND
