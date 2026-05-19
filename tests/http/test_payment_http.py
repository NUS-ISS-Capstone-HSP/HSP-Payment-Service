from fastapi.testclient import TestClient

from hsp_payment_service.repository.in_memory import (
    InMemoryEchoRepository,
    InMemoryPaymentRepository,
    InMemoryWorkerIncomeRepository,
)
from hsp_payment_service.service.echo_service import EchoService
from hsp_payment_service.service.payment_service import PaymentService
from hsp_payment_service.transport.http.app import create_http_app


def build_client() -> TestClient:
    echo_service = EchoService(InMemoryEchoRepository())
    payment_service = PaymentService(
        InMemoryPaymentRepository(), InMemoryWorkerIncomeRepository()
    )
    app = create_http_app(echo_service, payment_service)
    return TestClient(app)


def test_create_payment_http_success() -> None:
    client = build_client()
    response = client.post(
        "/api/payment/v1/payments",
        json={"order_id": "order-http", "amount": 150.0, "method": "CASH"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == "order-http"
    assert data["amount"] == 150.0
    assert data["method"] == "CASH"
    assert data["status"] == "PENDING"


def test_create_payment_http_duplicate_returns_409() -> None:
    client = build_client()
    client.post("/api/payment/v1/payments", json={"order_id": "dup", "amount": 100.0})
    response = client.post(
        "/api/payment/v1/payments", json={"order_id": "dup", "amount": 100.0}
    )

    assert response.status_code == 409


def test_get_payment_http_success() -> None:
    client = build_client()
    client.post(
        "/api/payment/v1/payments",
        json={"order_id": "get-test", "amount": 50.0},
    )

    response = client.get("/api/payment/v1/payments/get-test")

    assert response.status_code == 200
    assert response.json()["order_id"] == "get-test"


def test_get_payment_http_not_found_returns_404() -> None:
    client = build_client()
    response = client.get("/api/payment/v1/payments/no-such-order")
    assert response.status_code == 404


def test_process_callback_http_success() -> None:
    client = build_client()
    created = client.post(
        "/api/payment/v1/payments",
        json={"order_id": "cb-test", "amount": 100.0},
    ).json()

    response = client.post(
        "/api/payment/v1/payments/callback",
        json={"payment_id": created["payment_id"], "success": True},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


def test_calculate_income_http_success() -> None:
    client = build_client()
    response = client.post(
        "/api/payment/v1/incomes",
        json={
            "order_id": "inc-test",
            "worker_id": "worker-1",
            "order_amount": 100.0,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["worker_amount"] == 70.0
    assert data["commission_rate"] == 0.7


def test_revenue_summary_http_success() -> None:
    client = build_client()
    created = client.post(
        "/api/payment/v1/payments",
        json={"order_id": "rev-test", "amount": 100.0},
    ).json()
    client.post(
        "/api/payment/v1/payments/callback",
        json={"payment_id": created["payment_id"], "success": True},
    )
    client.post(
        "/api/payment/v1/incomes",
        json={
            "order_id": "rev-test",
            "worker_id": "w1",
            "order_amount": 100.0,
        },
    )

    response = client.get("/api/payment/v1/revenue-summary")

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["total_revenue"] == 100.0
    assert summary["paid_orders"] == 1
