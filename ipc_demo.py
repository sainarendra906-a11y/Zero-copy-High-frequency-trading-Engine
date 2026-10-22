
import mmap
import multiprocessing as mp
import os
import struct
import tempfile
import time

from src.models import ORDER_STRUCT, Order, Side


TOTAL_ORDERS = 1_000_000
RECORD_SIZE = ORDER_STRUCT.size


def producer(path, ready, done, error):
    """Write fixed-size binary order records into a memory-mapped file."""
    try:
        with open(path, "r+b") as file:
            with mmap.mmap(file.fileno(), 0) as mapped:
                for i in range(TOTAL_ORDERS):
                    offset = i * RECORD_SIZE

                    # Write directly into the mapped region.
                    ORDER_STRUCT.pack_into(
                        mapped,
                        offset,
                        i + 1,
                        10_000 + (i % 100),
                        1,
                        int(Side.BUY if i % 2 == 0 else Side.SELL),
                    )

                mapped.flush()

        ready.set()

    except Exception as exc:
        error.put(f"Producer error: {exc}")
        ready.set()


def consumer(path, ready, done, error):
    """Read and verify binary records from the mapped file."""
    try:
        ready.wait()

        with open(path, "r+b") as file:
            with mmap.mmap(file.fileno(), 0) as mapped:
                checksum = 0

                for i in range(TOTAL_ORDERS):
                    offset = i * RECORD_SIZE

                    # Unpack directly from mmap without slicing a bytes object.
                    order_id, price, quantity, side = (
                        ORDER_STRUCT.unpack_from(mapped, offset)
                    )

                    expected_side = (
                        int(Side.BUY) if i % 2 == 0 else int(Side.SELL)
                    )

                    if (
                        order_id != i + 1
                        or price != 10_000 + (i % 100)
                        or quantity != 1
                        or side != expected_side
                    ):
                        raise ValueError(f"Incorrect record at index {i}")

                    checksum += order_id

        expected_checksum = TOTAL_ORDERS * (TOTAL_ORDERS + 1) // 2

        if checksum != expected_checksum:
            raise ValueError("Checksum verification failed")

        done.put(
            f"Verified {TOTAL_ORDERS:,} orders. "
            f"Checksum: {checksum:,}"
        )

    except Exception as exc:
        error.put(f"Consumer error: {exc}")


def main():
    context = mp.get_context("spawn")
    ready = context.Event()
    done = context.Queue()
    errors = context.Queue()

    file_size = TOTAL_ORDERS * RECORD_SIZE

    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "orders.mmap")

        # Create the file once. Both processes open the same file.
        with open(path, "w+b") as file:
            file.truncate(file_size)

        consumer_process = context.Process(
            target=consumer,
            args=(path, ready, done, errors),
        )

        producer_process = context.Process(
            target=producer,
            args=(path, ready, done, errors),
        )

        start = time.perf_counter()

        consumer_process.start()
        producer_process.start()

        producer_process.join()
        consumer_process.join()

        elapsed = time.perf_counter() - start

        if not errors.empty():
            print(errors.get())
        elif not done.empty():
            print(done.get())
        else:
            print("ERROR: No verification result received.")

        print(f"Record size: {RECORD_SIZE} bytes")
        print(f"Total data: {file_size:,} bytes")
        print(f"Elapsed time: {elapsed:.3f} seconds")

        if elapsed > 0:
            print(f"Transfer rate: {TOTAL_ORDERS / elapsed:,.0f} records/sec")

        if producer_process.exitcode != 0:
            print("Producer process failed.")

        if consumer_process.exitcode != 0:
            print("Consumer process failed.")


if __name__ == "__main__":
    main()
