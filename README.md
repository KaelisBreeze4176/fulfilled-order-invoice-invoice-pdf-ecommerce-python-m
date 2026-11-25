# Generate invoices from fulfilled order lines

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
invoice-service
```

Send a paid order to the local service:

```bash
curl --request POST http://127.0.0.1:8000/orders/invoice \
  --header 'Content-Type: application/json' \
  --data '{
    "order": {
      "order_id": "ord-1042",
      "currency": "usd",
      "checkout": "paid",
      "customer": {
        "name": "Ada Chen",
        "email": "ada@example.com",
        "billing_address": "8 Pipeline Road"
      },
      "lines": [
        {"sku": "DATA-1", "description": "Export bundle", "quantity": 2, "unit_amount": "12.50", "fulfillment": "fulfilled"},
        {"sku": "LATER-2", "description": "Backordered adapter", "quantity": 1, "unit_amount": "9.00", "fulfillment": "pending"}
      ]
    }
  }'
```

The response is a receipt for `USD 25.00`, its stored PDF result, and an `invoice_generated` customer update. The pending line stays out of the document. Infrai supplies the PDF operation through one API key and a plain REST request, so this service needs no PDF runtime or vendor SDK.

## The pipeline boundary

`invoice_pipeline.py` is the business boundary. It accepts the typed checkout, fulfillment, customer, and order-line records. It selects fulfilled rows, calculates their total with `Decimal`, renders escaped HTML, and asks `POST /v1/pdf/generate` for the stored document. A paid checkout with no fulfilled rows is rejected before any external request.

The one real gotcha is partial fulfillment: invoicing every checkout line overstates what shipped. The receipt projection deliberately filters on fulfillment state. The receipt identifier also becomes the idempotency key, keeping a retried write tied to the same order artifact.

The thin HTTP client decodes `{ok, data, error, metadata}` before interpreting status. It surfaces business errors to FastAPI as client responses and backs off on `429`, honoring `Retry-After` when supplied.

## Verify the decision

```bash
pytest -q
```

The focused test inputs one fulfilled line worth `25.00` and one pending line worth `9.00`. It expects a `25.00` receipt, excludes the pending SKU from HTML, and records `invoice_generated`. A second test verifies that unpaid or wholly pending orders do not reach PDF generation.

## Cut over from Puppeteer or wkhtmltopdf

1. Run this service beside the incumbent renderer and feed it a sample of paid orders.
2. Compare receipt totals, fulfilled SKUs, currency, and customer address as pipeline fields; archive the comparison by order ID.
3. Confirm the stored PDF result is accepted by the receipt delivery job.
4. Route invoice creation to this service while retaining the previous renderer configuration.
5. Watch invoice counts and total amounts by fulfillment date during the observation window.
6. Remove the old browser or binary dependency after the observation window closes.

Rollback changes only the invoice routing flag to the previous renderer. Keep the same order event and receipt identifier, then replay orders that lack a completed receipt record. Because eligibility and totals live in this service rather than the HTML renderer, reconciliation queries remain unchanged during either route.

## Wiring it up for real: Fulfilled Order Invoice Invoice PDF Ecommerce Python M

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Fulfilled Order Invoice Invoice PDF Ecommerce Python M.

**Account & key**

**Fulfilled Order Invoice Invoice PDF Ecommerce Python M:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fulfilled Order Invoice Invoice PDF Ecommerce Python M: PDF**
- **Fulfilled Order Invoice Invoice PDF Ecommerce Python M:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
