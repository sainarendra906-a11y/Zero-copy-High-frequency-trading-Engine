
import struct

from ipc_ring_demo import (
    CAPACITY,
    FILE_SIZE,
    HEADER,
    HEADER_SIZE,
    RECORD_SIZE,
    TOTAL_ORDERS,
)
from src.models import ORDER_STRUCT, Order, Side


def test_ring_capacity_is_positive():
    assert CAPACITY > 0


def test_header_stores_two_unsigned_64_bit_indices():
    assert HEADER.format == "<QQ"
    assert HEADER.size == 16
    assert HEADER_SIZE == 16


def test_record_size_matches_order_struct():
    assert RECORD_SIZE == ORDER_STRUCT.size
    assert RECORD_SIZE == 21


def test_file_size_matches_ring_layout():
    assert FILE_SIZE == HEADER_SIZE + CAPACITY * RECORD_SIZE


def test_ring_can_hold_exactly_capacity_records():
    data = bytearray(FILE_SIZE)
    first_offset = HEADER_SIZE
    last_offset = HEADER_SIZE + (CAPACITY - 1) * RECORD_SIZE

    ORDER_STRUCT.pack_into(data, first_offset, 1, 10_000, 1, int(Side.BUY))
    ORDER_STRUCT.pack_into(
        data, last_offset, CAPACITY, 10_099, 1, int(Side.SELL)
    )

    first = Order.from_bytes(bytes(data[first_offset:first_offset + RECORD_SIZE]))
    last = Order.from_bytes(bytes(data[last_offset:last_offset + RECORD_SIZE]))

    assert first.order_id == 1
    assert first.side == Side.BUY
    assert last.order_id == CAPACITY
    assert last.side == Side.SELL


def test_expected_checksum_for_all_order_ids():
    expected = TOTAL_ORDERS * (TOTAL_ORDERS + 1) // 2

    assert expected == 500_000_500_000
