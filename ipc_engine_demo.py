
import mmap
import multiprocessing as mp
import os
import tempfile
import struct
import queue

from src.models import ORDER_STRUCT, Order, Side
from src.order_book import OrderBook


# Two orders for our end-to-end matching verification.
ORDERS = [
    Order(order_id=1, price=100, quantity=5, side=Side.SELL),
    Order(order_id=2, price=100, quantity=3, side=Side.BUY),
]

CAPACITY = 16
HEADER = struct.Struct("<QQ")
HEADER_SIZE = HEADER.size
RECORD_SIZE = ORDER_STRUCT.size
FILE_SIZE = HEADER_SIZE + CAPACITY * RECORD_SIZE


def producer(path, empty_slots, full_slots, lock, errors):
    """Write binary orders into the shared memory-mapped ring."""
    try:
        with open(path, "r+b") as file:
            with mmap.mmap(file.fileno(), FILE_SIZE) as mapped:
                for order in ORDERS:
                    if not empty_slots.acquire(timeout=10):
                        raise TimeoutError("No free ring-buffer slot")

                    with lock:
                        write_index, read_index = HEADER.unpack_from(
                            mapped, 0
                        )
                        offset = (
                            HEADER_SIZE + write_index * RECORD_SIZE
                        )

                        ORDER_STRUCT.pack_into(
                            mapped,
                            offset,
                            order.order_id,
                            order.price,
                            order.quantity,
                            int(order.side),
                        )

                        write_index = (write_index + 1) % CAPACITY
                        HEADER.pack_into(
                            mapped, 0, write_index, read_index
                        )

                    full_slots.release()

    except Exception as exc:
        errors.put(f"Producer error: {exc}")


def consumer(path, empty_slots, full_slots, lock, results, errors):
    """Read orders from the ring and submit them to OrderBook."""
    try:
        book = OrderBook()

        with open(path, "r+b") as file:
            with mmap.mmap(file.fileno(), FILE_SIZE) as mapped:
                for _ in ORDERS:
                    if not full_slots.acquire(timeout=10):
                        raise TimeoutError("No order became available")

                    with lock:
                        write_index, read_index = HEADER.unpack_from(
                            mapped, 0
                        )
                        offset = (
                            HEADER_SIZE + read_index * RECORD_SIZE
                        )

                        order_id, price, quantity, side_value = (
                            ORDER_STRUCT.unpack_from(mapped, offset)
                        )

                        read_index = (read_index + 1) % CAPACITY
                        HEADER.pack_into(
                            mapped, 0, write_index, read_index
                        )

                    empty_slots.release()

                    order = Order(
                        order_id=order_id,
                        price=price,
                        quantity=quantity,
                        side=Side(side_value),
                    )

                    book.add_order(order)

        trades = [
            {
                "buy_order_id": trade.buy_order_id,
                "sell_order_id": trade.sell_order_id,
                "price": trade.price,
                "quantity": trade.quantity,
            }
            for trade in book.trades
        ]

        best_ask = book.best_ask()

        results.put({
            "orders_processed": len(ORDERS),
            "trades": trades,
            "remaining_sell_quantity": (
                best_ask.quantity if best_ask else 0
            ),
        })

    except Exception as exc:
        errors.put(f"Consumer error: {exc}")


def main():
    ctx = mp.get_context("spawn")

    empty_slots = ctx.Semaphore(CAPACITY)
    full_slots = ctx.Semaphore(0)
    lock = ctx.Lock()
    results = ctx.Queue()
    errors = ctx.Queue()

    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "engine_ring.mmap")

        with open(path, "w+b") as file:
            file.truncate(FILE_SIZE)
            file.write(HEADER.pack(0, 0))

        consumer_process = ctx.Process(
            target=consumer,
            args=(
                path, empty_slots, full_slots,
                lock, results, errors,
            ),
        )
        producer_process = ctx.Process(
            target=producer,
            args=(
                path, empty_slots, full_slots,
                lock, errors,
            ),
        )

        consumer_process.start()
        producer_process.start()

        producer_process.join(timeout=15)
        consumer_process.join(timeout=15)

        # Detect a process that is stuck instead of waiting forever.
        for process in (producer_process, consumer_process):
            if process.is_alive():
                process.terminate()
                process.join()
                print(f"ERROR: {process.name} timed out.")

        error_messages = []
        while True:
            try:
                error_messages.append(errors.get_nowait())
            except queue.Empty:
                break

        if error_messages:
            for message in error_messages:
                print(message)
        elif (
            producer_process.exitcode != 0
            or consumer_process.exitcode != 0
        ):
            print("ERROR: A process failed.")
        else:
            try:
                result = results.get(timeout=2)
                print("ChronosMatch IPC + OrderBook Integration")
                print("-" * 45)
                print(f"Orders processed: {result['orders_processed']}")

                for trade in result["trades"]:
                    print(
                        f"TRADE: Buy #{trade['buy_order_id']} / "
                        f"Sell #{trade['sell_order_id']} | "
                        f"Price: {trade['price']} | "
                        f"Quantity: {trade['quantity']}"
                    )

                print(
                    "Remaining sell quantity: "
                    f"{result['remaining_sell_quantity']}"
                )

                if (
                    result["orders_processed"] == 2
                    and len(result["trades"]) == 1
                    and result["trades"][0]["quantity"] == 3
                    and result["remaining_sell_quantity"] == 2
                ):
                    print("END-TO-END VERIFICATION PASSED")
                else:
                    print("END-TO-END VERIFICATION FAILED")

            except queue.Empty:
                print("ERROR: No result received from the consumer.")

        results.close()
        errors.close()


if __name__ == "__main__":
    main()
