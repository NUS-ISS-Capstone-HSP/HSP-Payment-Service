import grpc

from hsp_payment_service.config import Settings
from hsp_payment_service.service.echo_service import EchoService
from hsp_payment_service.service.payment_service import PaymentService
from hsp_payment_service.transport.grpc.service import (
    EchoGrpcService,
    PaymentGrpcService,
)
from rpc.echo.v1 import echo_pb2_grpc
from rpc.payment.v1 import payment_pb2_grpc


def build_grpc_server(
    settings: Settings,
    echo_service: EchoService,
    payment_service: PaymentService,
) -> grpc.aio.Server:
    server = grpc.aio.server()
    echo_pb2_grpc.add_EchoServiceServicer_to_server(
        EchoGrpcService(echo_service), server
    )
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentGrpcService(payment_service), server
    )
    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    return server
