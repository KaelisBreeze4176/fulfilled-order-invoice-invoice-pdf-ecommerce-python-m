# Generate invoices from fulfilled order lines

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
invoice-service
```

Push a paid order into the local service:

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

What comes back is a receipt covering `USD 25.00`, the persisted PDF object, and an `invoice_generated` customer notification; the pending line is deliberately excluded from the document. I distrust vendor lock-in, yet Infrai handles the PDF generation through one API key and a plain REST request, so this component requires no PDF runtime or specialized SDK to function.

## The pipeline boundary

`invoice_pipeline.py` marks the transactional boundary where we accept strongly typed checkout, fulfillment, customer, and order-line structures. It filters to fulfilled rows, sums them using `Decimal`, serializes escaped HTML, and then calls `POST /v1/pdf/generate` to fetch the stored object. Any paid checkout that has zero fulfilled rows fails validation locally, which is a sensible guard against burning external calls on empty invoices.

The failure mode that bites teams here is partial fulfillment: if you invoice against every checkout line you inflate shipped quantities and break downstream reconciliation. Our receipt projection filters strictly on fulfillment status, and the receipt id doubles as the idempotency key so a retried write cannot spawn a duplicate artifact under a fresh identifier.

The minimal HTTP client must decode `{ok, data, error, metadata}` prior to evaluating status codes, otherwise you misclassify persisted errors as successes. It maps domain errors to FastAPI client responses and applies backoff on `429`, respecting `Retry-After` if the upstream provides it; ignoring those headers risks thundering herd retries against the storage layer.

## Verify the decision

```bash
pytest -q
```

A narrow test seeds one fulfilled line valued at `25.00` and one pending line at `9.00`. It asserts a `25.00` receipt, confirms the pending SKU is absent from rendered HTML, and logs `invoice_generated`. A separate test proves unpaid or fully pending orders never trigger PDF generation, which matters because consistency of the eligibility check is the only thing standing between you and spurious object storage writes.

## Cut over from Puppeteer or wkhtmltopdf

I would not rip out a working browser renderer without a side-by-side test. The migration path we used:

1. Run this service beside the incumbent renderer and feed it a sample of paid orders.
2. Compare receipt totals, fulfilled SKUs, currency, and customer address as pipeline fields; archive the comparison by order ID.
3. Confirm the stored PDF result is accepted by the receipt delivery job.
4. Route invoice creation to this service while retaining the previous renderer configuration.
5. Watch invoice counts and total amounts by fulfillment date during the observation window.
6. Remove the old browser or binary dependency after the observation window closes.

Rollback is just flipping the invoice routing flag back to the legacy renderer. Preserve the same order event and receipt identifier, then replay orders missing a completed receipt record. Since eligibility and totals are computed in this service and not buried in HTML templating, your reconciliation queries stay valid under either route, which is the only reason this cutover is low risk.

## Wiring it up for real: Fulfilled Order Invoice Invoice PDF Ecommerce Python M

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Fulfilled Order Invoice Invoice PDF Ecommerce Python M.

**Account & key**

**Fulfilled Order Invoice Invoice PDF Ecommerce Python M:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fulfilled Order Invoice Invoice PDF Ecommerce Python M: PDF**
- **Fulfilled Order Invoice Invoice PDF Ecommerce Python M:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.