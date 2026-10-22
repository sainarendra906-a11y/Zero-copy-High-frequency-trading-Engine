
import mmap
import multiprocessing as mp
import os
import struct
import tempfile
import time

from src.models import ORDER_STRUCT, Side


TOTAL_ORDERS = 1_000_000
CAPACITY = 4096
HEADER = struct.Struct("<QQ")
HEADER_SIZE = HEADER.size
RECORD_SIZE = ORDER_STRUCT.size
FILE_SIZE = HEADER_SIZE + CAPACITY * RECORD_SIZE


def producer(path, empty_slots, full_slots, lock, errors):
    """Produce binary orders into a shared memory-mapped ring."""
    try:
        with open(path, "r+b") as file:
            with mmap.mmap(file.fileno(), FILE_SIZE) as mapped:
                for i in range(TOTAL_ORDERS):
                    # Wait until at least one slot is free.
                    empty_slots.acquire()

                    with lock:
                        write_index, read_index = HEADER.unpack_from(mapped, 0)
                        offset = HEADER_SIZE + write_index * RECORD_SIZE

                        # Write directly into the mapped memory.
                        ORDER_STRUCT.pack_into(
                            mapped,
                            offset,
                            i + 1,
                            10_000 + (i % 100),
                            1,
                            int(Side.BUY if i % 2 == 0 else Side.SELL),
                        )

                        write_index = (write_index + 1) % CAPACITY
                        HEADER.pack_into(
                            mapped, 0, write_index, read_index
                        )

                    # Tell the consumer that one record is ready.
                    full_slots.release()

                mapped.flush()

    except Exception as exc:
        errors.put(f"Producer error: {exc}")


def consumer(path, empty_slots, full_slots, lock, results, errors):
    """Consume and verify records from the shared ring."""
    try:
        checksum = 0

        with open(path, "r+b") as file:
            with mmap.mmap(file.fileno(), FILE_SIZE) as mapped:
                for i in range(TOTAL_ORDERS):
                    # Wait until a record is available.
                    full_slots.acquire()

                    with lock:
                        write_index, read_index = HEADER.unpack_from(mapped, 0)
                        offset = HEADER_SIZE + read_index * RECORD_SIZE

                        # Decode directly from mmap, without a bytes slice.
                        order_id, price, quantity, side = (
                            ORDER_STRUCT.unpack_from(mapped, offset)
                        )

                        expected_side = (
                            int(Side.BUY)
                            if i % 2 == 0
                            else int(Side.SELL)
                        )

                        if (
                            order_id != i + 1
                            or price != 10_000 + (i % 100)
                            or quantity != 1
                            or side != expected_side
                        ):
                            raise ValueError(
                                f"Invalid order at position {i}: "
                                f"id={order_id}, price={price}, "
                                f"quantity={quantity}, side={side}"
                            )

                        checksum += order_id
                        read_index = (read_index + 1) % CAPACITY

                        HEADER.pack_into(
                            mapped, 0, write_index, read_index
                        )

                    # Tell the producer that one slot is free.
                    empty_slots.release()

        expected_checksum = TOTAL_ORDERS * (TOTAL_ORDERS + 1) // 2

        if checksum != expected_checksum:
            raise ValueError(
                f"Checksum mismatch: {checksum} != {expected_checksum}"
            )

        results.put(
            f"Verified {TOTAL_ORDERS:,} orders. "
            f"Checksum: {checksum:,}"
        )

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
        path = os.path.join(temp_dir, "shared_ring.mmap")

        # Initialize the shared file and ring indices.
        with open(path, "w+b") as file:
            file.truncate(FILE_SIZE)
            file.seek(0)
            file.write(HEADER.pack(0, 0))

        consumer_process = ctx.Process(
            target=consumer,
            args=(path, empty_slots, full_slots, lock, results, errors),
        )
        producer_process = ctx.Process(
            target=producer,
            args=(path, empty_slots, full_slots, lock, errors),
        )

        start = time.perf_counter()

        # Start the consumer first so it can wait for incoming orders.
        consumer_process.start()
        producer_process.start()

        producer_process.join()
        consumer_process.join()

        elapsed = time.perf_counter() - start

        if not errors.empty():
            print(errors.get())
        elif not results.empty():
            print(results.get())
        else:
            print("ERROR: No verification result received.")

        print(f"Record size: {RECORD_SIZE} bytes")
        print(f"Ring capacity: {CAPACITY:,} orders")
        print(f"Orders transferred: {TOTAL_ORDERS:,}")
        print(f"Elapsed time: {elapsed:.3f} seconds")

        if elapsed > 0:
            print(
                f"Transfer rate: "
                f"{TOTAL_ORDERS / elapsed:,.0f} orders/sec"
            )

        if (
            producer_process.exitcode != 0
            or consumer_process.exitcode != 0
        ):
            print("ERROR: One or both processes failed.")


if __name__ == "__main__":
    main()
