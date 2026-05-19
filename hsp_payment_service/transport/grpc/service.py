import grpc

from hsp_payment_service.domain.errors import (
    DuplicateError,
    NotFoundError,
    ValidationError,
)
from hsp_payment_service.domain.models import SourceType
from hsp_payment_service.service.echo_service import EchoService
from hsp_payment_service.service.payment_service import PaymentService
from hsp_payment_service.transport.grpc.mapper import (
    method_from_proto,
    to_grpc_payment,
    to_grpc_record,
    to_grpc_worker_income,
)
from rpc.echo.v1 import echo_pb2, echo_pb2_grpc
from rpc.payment.v1 import payment_pb2, payment_pb2_grpc


class EchoGrpcService(echo_pb2_grpc.EchoServiceServicer):
    def __init__(self, echo_service: EchoService) -> None:
        self._echo_service = echo_service

    async def CreateEcho(self, request, context):
        try:
            record = await self._echo_service.create_echo(
                request.message, SourceType.GRPC
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        return echo_pb2.CreateEchoResponse(record=to_grpc_record(record))

    async def GetEcho(self, request, context):
        try:
            record = await self._echo_service.get_echo(request.id)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return echo_pb2.GetEchoResponse(record=to_grpc_record(record))

    async def Health(self, request, context):
        del request, context
        return echo_pb2.HealthResponse(status="ok")


class PaymentGrpcService(payment_pb2_grpc.PaymentServiceServicer):
    def __init__(self, payment_service: PaymentService) -> None:
        self._payment_service = payment_service

    async def CreatePayment(self, request, context):
        try:
            method = method_from_proto(request.method)
            payment = await self._payment_service.create_payment(
                order_id=request.order_id,
                amount=request.amount,
                method=method,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except DuplicateError as exc:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
        return payment_pb2.CreatePaymentResponse(payment=to_grpc_payment(payment))

    async def GetPayment(self, request, context):
        try:
            payment = await self._payment_service.get_payment(request.order_id)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return payment_pb2.GetPaymentResponse(payment=to_grpc_payment(payment))

    async def ProcessPaymentCallback(self, request, context):
        try:
            payment = await self._payment_service.process_payment_callback(
                payment_id=request.payment_id,
                success=request.success,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return payment_pb2.ProcessPaymentCallbackResponse(
            payment=to_grpc_payment(payment)
        )

    async def CalculateWorkerIncome(self, request, context):
        try:
            income = await self._payment_service.calculate_worker_income(
                order_id=request.order_id,
                worker_id=request.worker_id,
                order_amount=request.order_amount,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        return payment_pb2.CalculateWorkerIncomeResponse(
            income=to_grpc_worker_income(income)
        )

    async def GetRevenueSummary(self, request, context):
        total_revenue, total_payout, net, orders, paid, incomes = (
            await self._payment_service.get_revenue_summary(
                start_date=request.start_date,
                end_date=request.end_date,
            )
        )
        summary = payment_pb2.RevenueSummary(
            total_revenue=total_revenue,
            total_worker_payout=total_payout,
            net_income=net,
            total_orders=orders,
            paid_orders=paid,
        )
        return payment_pb2.GetRevenueSummaryResponse(
            summary=summary,
            incomes=[to_grpc_worker_income(i) for i in incomes],
        )

    async def Health(self, request, context):
        del request, context
        return payment_pb2.HealthResponse(status="ok")
