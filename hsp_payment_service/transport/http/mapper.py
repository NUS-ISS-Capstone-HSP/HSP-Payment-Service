from hsp_payment_service.domain.models import EchoRecord, Payment, WorkerIncome
from hsp_payment_service.transport.http.schemas import (
    EchoRecordResponse,
    PaymentResponse,
    RevenueSummaryResponse,
    WorkerIncomeResponse,
)


def to_http_response(record: EchoRecord) -> EchoRecordResponse:
    return EchoRecordResponse(
        id=record.id,
        message=record.message,
        source=record.source.value,
        created_at=record.created_at.isoformat(),
    )


def to_payment_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        payment_id=payment.payment_id,
        order_id=payment.order_id,
        amount=payment.amount,
        method=payment.method.value,
        status=payment.status.value,
        paid_at=payment.paid_at.isoformat() if payment.paid_at else None,
        created_at=payment.created_at.isoformat(),
        updated_at=payment.updated_at.isoformat(),
    )


def to_worker_income_response(income: WorkerIncome) -> WorkerIncomeResponse:
    return WorkerIncomeResponse(
        income_id=income.income_id,
        order_id=income.order_id,
        worker_id=income.worker_id,
        order_amount=income.order_amount,
        commission_rate=income.commission_rate,
        worker_amount=income.worker_amount,
        settled=income.settled,
        settled_at=income.settled_at.isoformat() if income.settled_at else None,
        created_at=income.created_at.isoformat(),
    )


def to_revenue_summary_response(
    total_revenue: float,
    total_payout: float,
    net: float,
    orders: int,
    paid: int,
    incomes: list[WorkerIncome],
) -> GetRevenueSummaryResponse:
    return GetRevenueSummaryResponse(
        summary=RevenueSummaryResponse(
            total_revenue=total_revenue,
            total_worker_payout=total_payout,
            net_income=net,
            total_orders=orders,
            paid_orders=paid,
        ),
        incomes=[to_worker_income_response(i) for i in incomes],
    )
