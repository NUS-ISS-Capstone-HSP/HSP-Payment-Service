from pydantic import BaseModel, ConfigDict, Field


class CreateEchoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Hello from HTTP"}},
    )

    message: str = Field(
        min_length=1,
        max_length=2048,
        description="Message content to be stored as an echo record.",
    )


class EchoRecordResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "6f88f9f2-65fd-4ef7-80de-2c96d8ab7b5b",
                "message": "Hello from HTTP",
                "source": "HTTP",
                "created_at": "2026-03-18T12:34:56+00:00",
            }
        },
    )

    id: str = Field(description="Echo record id (UUID).")
    message: str = Field(description="Stored message.")
    source: str = Field(description="Record source. HTTP or GRPC.")
    created_at: str = Field(description="Creation time in ISO-8601 format.")


# ── Payment schemas ──


class CreatePaymentRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "uuid-order-xxxx",
                "amount": 299.00,
                "method": "WECHAT",
            }
        },
    )
    order_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    method: str = Field(default="WECHAT", description="WECHAT | CASH")


class PaymentResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "payment_id": "uuid-payment-xxxx",
                "order_id": "uuid-order-xxxx",
                "amount": 299.00,
                "method": "WECHAT",
                "status": "PENDING",
                "paid_at": None,
                "created_at": "2026-04-01T10:00:00+00:00",
                "updated_at": "2026-04-01T10:00:00+00:00",
            }
        },
    )
    payment_id: str
    order_id: str
    amount: float
    method: str
    status: str
    paid_at: str | None = None
    created_at: str
    updated_at: str


class ProcessPaymentCallbackRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"payment_id": "uuid-payment-xxxx", "success": True}
        },
    )
    payment_id: str = Field(min_length=1)
    success: bool


class CalculateWorkerIncomeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "uuid-order-xxxx",
                "worker_id": "worker-1001",
                "order_amount": 299.00,
            }
        },
    )
    order_id: str = Field(min_length=1)
    worker_id: str = Field(min_length=1)
    order_amount: float = Field(gt=0)


class WorkerIncomeResponse(BaseModel):
    income_id: str
    order_id: str
    worker_id: str
    order_amount: float
    commission_rate: float
    worker_amount: float
    settled: str
    settled_at: str | None = None
    created_at: str


class RevenueSummaryResponse(BaseModel):
    total_revenue: float
    total_worker_payout: float
    net_income: float
    total_orders: int
    paid_orders: int


class GetRevenueSummaryResponse(BaseModel):
    summary: RevenueSummaryResponse
    incomes: list[WorkerIncomeResponse]
