from hsp_payment_service.domain.models import (
    EchoRecord,
    Payment,
    PaymentMethod,
    PaymentStatus,
    WorkerIncome,
)
from rpc.echo.v1 import echo_pb2
from rpc.payment.v1 import payment_pb2


def to_grpc_record(record: EchoRecord) -> echo_pb2.EchoRecord:
    return echo_pb2.EchoRecord(
        id=record.id,
        message=record.message,
        source=record.source.value,
        created_at=record.created_at.isoformat(),
    )


_PROTO_METHOD: dict[PaymentMethod, int] = {
    PaymentMethod.WECHAT: payment_pb2.PAYMENT_METHOD_WECHAT,
    PaymentMethod.CASH: payment_pb2.PAYMENT_METHOD_CASH,
}

_PROTO_STATUS: dict[PaymentStatus, int] = {
    PaymentStatus.PENDING: payment_pb2.PAYMENT_STATUS_PENDING,
    PaymentStatus.COMPLETED: payment_pb2.PAYMENT_STATUS_COMPLETED,
    PaymentStatus.FAILED: payment_pb2.PAYMENT_STATUS_FAILED,
    PaymentStatus.REFUNDED: payment_pb2.PAYMENT_STATUS_REFUNDED,
}

_METHOD_REVERSE: dict[int, PaymentMethod] = {
    payment_pb2.PAYMENT_METHOD_WECHAT: PaymentMethod.WECHAT,
    payment_pb2.PAYMENT_METHOD_CASH: PaymentMethod.CASH,
}

_STATUS_REVERSE: dict[int, PaymentStatus] = {
    payment_pb2.PAYMENT_STATUS_PENDING: PaymentStatus.PENDING,
    payment_pb2.PAYMENT_STATUS_COMPLETED: PaymentStatus.COMPLETED,
    payment_pb2.PAYMENT_STATUS_FAILED: PaymentStatus.FAILED,
    payment_pb2.PAYMENT_STATUS_REFUNDED: PaymentStatus.REFUNDED,
}


def to_grpc_payment(payment: Payment) -> payment_pb2.Payment:
    return payment_pb2.Payment(
        payment_id=payment.payment_id,
        order_id=payment.order_id,
        amount=payment.amount,
        method=_PROTO_METHOD.get(payment.method, 0),
        status=_PROTO_STATUS.get(payment.status, 0),
        paid_at=payment.paid_at.isoformat() if payment.paid_at else "",
        created_at=payment.created_at.isoformat(),
        updated_at=payment.updated_at.isoformat(),
    )


def to_grpc_worker_income(income: WorkerIncome) -> payment_pb2.WorkerIncome:
    return payment_pb2.WorkerIncome(
        income_id=income.income_id,
        order_id=income.order_id,
        worker_id=income.worker_id,
        order_amount=income.order_amount,
        commission_rate=income.commission_rate,
        worker_amount=income.worker_amount,
        settled=income.settled,
        settled_at=income.settled_at.isoformat() if income.settled_at else "",
        created_at=income.created_at.isoformat(),
    )


def method_from_proto(proto_val: int) -> PaymentMethod:
    return _METHOD_REVERSE.get(proto_val, PaymentMethod.WECHAT)
