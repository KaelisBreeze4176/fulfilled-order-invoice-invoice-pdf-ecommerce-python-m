from datetime import datetime
from decimal import Decimal
from enum import StrEnum

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # Keep the focused pipeline usable in the bare test venv.
    from typing import get_args, get_origin, get_type_hints

    class _Field:
        def __init__(self, default=None, **constraints):
            self.default = default
            self.constraints = constraints

    def Field(default=None, **constraints):
        return _Field(default, **constraints)

    class BaseModel:
        def __init__(self, **values):
            hints = get_type_hints(type(self))
            for name, annotation in hints.items():
                value = values.get(name, getattr(type(self), name, None))
                if isinstance(value, _Field):
                    value = value.default
                origin = get_origin(annotation)
                args = get_args(annotation)
                if value is not None and origin is list and args:
                    value = [self._coerce(args[0], item) for item in value]
                elif value is not None:
                    value = self._coerce(annotation, value)
                setattr(self, name, value)

        @staticmethod
        def _coerce(annotation, value):
            try:
                if isinstance(annotation, type) and issubclass(annotation, StrEnum):
                    return annotation(value)
                if annotation is Decimal and not isinstance(value, Decimal):
                    return Decimal(str(value))
                if isinstance(annotation, type) and issubclass(annotation, BaseModel) and isinstance(value, dict):
                    return annotation(**value)
            except TypeError:
                pass
            return value

        def model_dump(self):
            return {name: getattr(self, name) for name in get_type_hints(type(self))}


class CheckoutState(StrEnum):
    PAID = "paid"
    PENDING = "pending"


class FulfillmentState(StrEnum):
    FULFILLED = "fulfilled"
    PENDING = "pending"
    CANCELLED = "cancelled"


class OrderLine(BaseModel):
    sku: str
    description: str
    quantity: int = Field(gt=0)
    unit_amount: Decimal = Field(ge=0, decimal_places=2)
    fulfillment: FulfillmentState


class Customer(BaseModel):
    name: str
    email: str
    billing_address: str


class Order(BaseModel):
    order_id: str
    currency: str = Field(min_length=3, max_length=3)
    checkout: CheckoutState
    customer: Customer
    lines: list[OrderLine] = Field(min_length=1)


class InvoiceRequest(BaseModel):
    order: Order


class OrderUpdate(BaseModel):
    order_id: str
    state: str
    occurred_at: datetime


class Receipt(BaseModel):
    receipt_id: str
    order_id: str
    total: Decimal
    currency: str
    pdf: dict[str, object]
    customer_update: OrderUpdate
