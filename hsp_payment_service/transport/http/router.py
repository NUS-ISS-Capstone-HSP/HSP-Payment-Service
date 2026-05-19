from fastapi import APIRouter, Path, Query

from hsp_payment_service.domain.models import PaymentMethod, SourceType
from hsp_payment_service.service.echo_service import EchoService
from hsp_payment_service.service.payment_service import PaymentService
from hsp_payment_service.transport.http.mapper import (
    to_http_response,
    to_payment_response,
    to_revenue_summary_response,
    to_worker_income_response,
)
from hsp_payment_service.transport.http.schemas import (
    CalculateWorkerIncomeRequest,
    CreateEchoRequest,
    CreatePaymentRequest,
    EchoRecordResponse,
    GetRevenueSummaryResponse,
    PaymentResponse,
    ProcessPaymentCallbackRequest,
    WorkerIncomeResponse,
)


def build_router(
    echo_service: EchoService, payment_service: PaymentService
) -> APIRouter:
    router = APIRouter(prefix="/api/payment/v1", tags=["payment"])

    # ── Echo ──

    @router.post("/echo", response_model=EchoRecordResponse, status_code=201)
    async def create_echo(payload: CreateEchoRequest) -> EchoRecordResponse:
        record = await echo_service.create_echo(payload.message, SourceType.HTTP)
        return to_http_response(record)

    @router.get("/echo/{echo_id}", response_model=EchoRecordResponse)
    async def get_echo(echo_id: str = Path(...)) -> EchoRecordResponse:
        record = await echo_service.get_echo(echo_id)
        return to_http_response(record)

    # ── Payments ──

    @router.post("/payments", response_model=PaymentResponse, status_code=201)
    async def create_payment(payload: CreatePaymentRequest) -> PaymentResponse:
        method = PaymentMethod(payload.method.upper())
        payment = await payment_service.create_payment(
            order_id=payload.order_id,
            amount=payload.amount,
            method=method,
        )
        return to_payment_response(payment)

    @router.get("/payments/{order_id}", response_model=PaymentResponse)
    async def get_payment(order_id: str = Path(...)) -> PaymentResponse:
        payment = await payment_service.get_payment(order_id)
        return to_payment_response(payment)

    @router.post(
        "/payments/callback", response_model=PaymentResponse
    )
    async def process_payment_callback(
        payload: ProcessPaymentCallbackRequest,
    ) -> PaymentResponse:
        payment = await payment_service.process_payment_callback(
            payment_id=payload.payment_id,
            success=payload.success,
        )
        return to_payment_response(payment)

    @router.post("/incomes", response_model=WorkerIncomeResponse, status_code=201)
    async def calculate_worker_income(
        payload: CalculateWorkerIncomeRequest,
    ) -> WorkerIncomeResponse:
        income = await payment_service.calculate_worker_income(
            order_id=payload.order_id,
            worker_id=payload.worker_id,
            order_amount=payload.order_amount,
        )
        return to_worker_income_response(income)

    @router.get(
        "/revenue-summary", response_model=GetRevenueSummaryResponse
    )
    async def get_revenue_summary(
        start_date: str = Query(default=""),
        end_date: str = Query(default=""),
    ) -> GetRevenueSummaryResponse:
        total_rev, total_payout, net, orders, paid, incomes = (
            await payment_service.get_revenue_summary(start_date, end_date)
        )
        return to_revenue_summary_response(
            total_rev, total_payout, net, orders, paid, incomes
        )

    return router
