
import asyncio
import time

from src.models import Order, Side
from src.order_book import OrderBook


TOTAL_ORDERS = 100_000
TARGET_RATE = 100_000
QUEUE_CAPACITY = 10_000


async def run_market_engine():
    book = OrderBook()
    queue = asyncio.Queue(maxsize=QUEUE_CAPACITY)
    processed = 0

    async def feed():
        """Generate and enqueue orders at the target rate."""
        start = time.perf_counter()

        for i in range(TOTAL_ORDERS):
            order = Order(
                order_id=i + 1,
                price=10_000,
                quantity=1,
                side=Side.BUY if i % 2 == 0 else Side.SELL,
            )

            await queue.put(order)

            # Pace the feed against a target of 100,000 orders/sec.
            deadline = start + (i + 1) / TARGET_RATE
            delay = deadline - time.perf_counter()

            if delay > 0:
                await asyncio.sleep(delay)

        await queue.put(None)

    async def engine():
        """Consume queued orders and submit them to OrderBook."""
        nonlocal processed

        while True:
            order = await queue.get()

            try:
                if order is None:
                    return

                book.add_order(order)
                processed += 1
            finally:
                queue.task_done()

    start = time.perf_counter()

    await asyncio.gather(feed(), engine())

    elapsed = time.perf_counter() - start
    actual_rate = processed / elapsed if elapsed > 0 else 0

    print("ChronosMatch Market Feed + Matching Engine")
    print("-" * 45)
    print(f"Orders processed: {processed:,}")
    print(f"Trades executed: {len(book.trades):,}")
    print(f"Target rate: {TARGET_RATE:,} orders/sec")
    print(f"Elapsed time: {elapsed:.3f} seconds")
    print(f"End-to-end rate: {actual_rate:,.0f} orders/sec")
    print(f"Remaining buy orders: {len(book.bids)}")
    print(f"Remaining sell orders: {len(book.asks)}")

    passed = (
        processed == TOTAL_ORDERS
        and len(book.trades) == TOTAL_ORDERS // 2
        and not book.bids
        and not book.asks
    )

    print(
        "ENGINE VERIFICATION PASSED"
        if passed
        else "ENGINE VERIFICATION FAILED"
    )


if __name__ == "__main__":
    asyncio.run(run_market_engine())
