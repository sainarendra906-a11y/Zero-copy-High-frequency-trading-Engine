
import struct
from dataclasses import dataclass
from enum import IntEnum


class Side(IntEnum):
    BUY = 1
    SELL = 2


# Fixed-size binary record:
# order_id (unsigned 64-bit), price (unsigned 64-bit),
# quantity (unsigned 32-bit), side (unsigned 8-bit)
ORDER_STRUCT = struct.Struct("<QQIB")


@dataclass(frozen=True, slots=True)
class Order:
    order_id: int
    price: int
    quantity: int
    side: Side

    def __post_init__(self):
        if not 0 <= self.order_id <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("order_id must fit in an unsigned 64-bit integer")
        if not 1 <= self.price <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("price must be a positive unsigned 64-bit integer")
        if not 1 <= self.quantity <= 0xFFFFFFFF:
            raise ValueError("quantity must fit in an unsigned 32-bit integer")
        if not isinstance(self.side, Side):
            raise ValueError("side must be Side.BUY or Side.SELL")

    def to_bytes(self) -> bytes:
        return ORDER_STRUCT.pack(
            self.order_id,
            self.price,
            self.quantity,
            int(self.side),
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "Order":
        if len(data) != ORDER_STRUCT.size:
            raise ValueError(
                f"Expected {ORDER_STRUCT.size} bytes, got {len(data)}"
            )

        order_id, price, quantity, side_value = ORDER_STRUCT.unpack(data)

        try:
            side = Side(side_value)
        except ValueError as exc:
            raise ValueError(f"Invalid order side: {side_value}") from exc

        return cls(order_id, price, quantity, side)
