from fastapi import FastAPI, HTTPException

from infrai_pdf import InfraiError, InfraiPdfClient
from invoice_pipeline import InvoiceDecisionError, build_fulfilled_receipt
from order_models import InvoiceRequest, Receipt

service = FastAPI(title="Fulfilled order invoice service")


@service.post("/orders/invoice", response_model=Receipt)
def create_invoice(request: InvoiceRequest) -> Receipt:
    client = InfraiPdfClient()
    try:
        return build_fulfilled_receipt(request.order, client)
    except InvoiceDecisionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
    finally:
        client.close()


def run() -> None:
    import uvicorn

    uvicorn.run("invoice_service:service", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
