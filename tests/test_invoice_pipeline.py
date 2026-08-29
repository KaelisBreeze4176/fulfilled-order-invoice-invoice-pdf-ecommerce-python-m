from decimal import Decimal

import pytest

from invoice_pipeline import InvoiceDecisionError, build_fulfilled_receipt
from order_models import Customer, Order, OrderLine


class RecordingPdfClient:
    def __init__(self) -> None:
        self.html = ""
        self.idempotency_key = ""

    def generate_invoice(self, html: str, idempotency_key: str) -> dict[str, object]:
        self.html = html
        self.idempotency_key = idempotency_key
        return {"url": "https://downloads.example/receipt.pdf"}


def order_with(checkout: str = "paid", first_state: str = "fulfilled") -> Order:
    return Order(
        order_id="ord-1042",
        currency="usd",
        checkout=checkout,
        customer=Customer(
            name="Ada Chen",
            email="ada@example.com",
            billing_address="8 Pipeline Road",
        ),
        lines=[
            OrderLine(
                sku="DATA-1",
                description="Export bundle",
                quantity=2,
                unit_amount=Decimal("12.50"),
                fulfillment=first_state,
            ),
            OrderLine(
                sku="LATER-2",
                description="Backordered adapter",
                quantity=1,
                unit_amount=Decimal("9.00"),
                fulfillment="pending",
            ),
        ],
    )


def test_receipt_contains_only_fulfilled_lines_and_emits_update() -> None:
    client = RecordingPdfClient()

    receipt = build_fulfilled_receipt(order_with(), client)

    assert receipt.total == Decimal("25.00")
    assert receipt.customer_update.state == "invoice_generated"
    assert "Export bundle" in client.html
    assert "Backordered adapter" not in client.html
    assert client.idempotency_key == "receipt-ord-1042"


@pytest.mark.parametrize(
    ("checkout", "fulfillment"),
    [("pending", "fulfilled"), ("paid", "pending")],
)
def test_receipt_rejects_ineligible_orders(checkout: str, fulfillment: str) -> None:
    with pytest.raises(InvoiceDecisionError):
        build_fulfilled_receipt(
            order_with(checkout=checkout, first_state=fulfillment), RecordingPdfClient()
        )
