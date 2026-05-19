from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from hsp_payment_service.domain.errors import (
    DomainError,
    DuplicateError,
    NotFoundError,
    ValidationError,
)
from hsp_payment_service.service.echo_service import EchoService
from hsp_payment_service.service.payment_service import PaymentService
from hsp_payment_service.transport.http.router import build_router


def create_http_app(
    echo_service: EchoService, payment_service: PaymentService
) -> FastAPI:
    app = FastAPI(title="HSP Payment Service")
    app.include_router(build_router(echo_service, payment_service))

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(ValidationError)
    async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DuplicateError)
    async def duplicate_handler(_: Request, exc: DuplicateError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def domain_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    return app
