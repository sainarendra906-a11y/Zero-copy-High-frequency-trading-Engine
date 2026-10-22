
import asyncio
import time

from src.models import Order, Side


async def market_feed(
    number_of_orders: int = 100_000,
    target_rate: int = 100_000,
):
    """Generate simulated market orders asynchronously."""
    if number_of_orders <= 0:
        raise ValueError("number_of_orders must be positive")
    if target_rate <= 0:
        raise ValueError("target_rate must be positive")

    interval = 1 / target_rate
    start = time.perf_counter()
    next_order_time = start

    generated = 0

    for i in range(number_of_orders):
        order = Order(
            order_id=i + 1,
            price=10_000 + (i % 100),
            quantity=1 + (i % 10),
            side=Side.BUY if i % 2 == 0 else Side.SELL,
        )

        # Yield control to the event loop periodically.
        if i % 100 == 0:
            await asyncio.sleep(0)

        # Pace the feed toward the requested rate.
        next_order_time += interval
        delay = next_order_time - time.perf_counter()

        if delay > 0:
            await asyncio.sleep(delay)

        generated += 1

    elapsed = time.perf_counter() - start
    actual_rate = generated / elapsed if elapsed > 0 else 0

    print("ChronosMatch Async Market Feed")
    print("-" * 35)
    print(f"Orders generated: {generated:,}")
    print(f"Elapsed time: {elapsed:.3f} seconds")
    print(f"Target rate: {target_rate:,} orders/sec")
    print(f"Actual rate: {actual_rate:,.0f} orders/sec")

    return generated


if __name__ == "__main__":
    asyncio.run(market_feed())
