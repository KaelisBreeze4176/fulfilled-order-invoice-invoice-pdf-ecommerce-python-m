from datetime import datetime, timezone
from decimal import Decimal
from html import escape
from typing import Protocol

from order_models import CheckoutState, FulfillmentState, Order, OrderUpdate, Receipt


class InvoiceDecisionError(ValueError):
    pass


class PdfGenerator(Protocol):
    def generate_invoice(self, html: str, idempotency_key: str) -> dict[str, object]:
        return {}


def build_fulfilled_receipt(order: Order, client: PdfGenerator) -> Receipt:
    if order.checkout != CheckoutState.PAID:
        raise InvoiceDecisionError("checkout must be paid before invoicing")

    fulfilled = [line for line in order.lines if line.fulfillment == FulfillmentState.FULFILLED]
    if not fulfilled:
        raise InvoiceDecisionError("at least one fulfilled line is required")

    total = sum(
        (line.unit_amount * line.quantity for line in fulfilled),
        start=Decimal("0.00"),
    )
    receipt_id = f"receipt-{order.order_id}"
    rows = "".join(
        "<tr>"
        f"<td>{escape(line.sku)}</td>"
        f"<td>{escape(line.description)}</td>"
        f"<td>{line.quantity}</td>"
        f"<td>{line.unit_amount:.2f}</td>"
        f"<td>{line.unit_amount * line.quantity:.2f}</td>"
        "</tr>"
        for line in fulfilled
    )
    html = f"""<!doctype html>
<html><body>
<h1>Receipt {escape(receipt_id)}</h1>
<p>Order: {escape(order.order_id)}</p>
<p>Bill to: {escape(order.customer.name)}<br>{escape(order.customer.billing_address)}</p>
<table><thead><tr><th>SKU</th><th>Item</th><th>Qty</th><th>Unit</th><th>Line total</th></tr></thead>
<tbody>{rows}</tbody></table>
<p>Total: {escape(order.currency.upper())} {total:.2f}</p>
</body></html>"""
    pdf = client.generate_invoice(html, idempotency_key=receipt_id)
    update = OrderUpdate(
        order_id=order.order_id,
        state="invoice_generated",
        occurred_at=datetime.now(timezone.utc),
    )
    return Receipt(
        receipt_id=receipt_id,
        order_id=order.order_id,
        total=total,
        currency=order.currency.upper(),
        pdf=pdf,
        customer_update=update,
    )
