
import statistics
import time

from src.models import Order, Side
from src.order_book import OrderBook


def run_benchmark(number_of_orders=10_000):
    book = OrderBook()
    latencies_ns = []

    start = time.perf_counter_ns()

    for i in range(number_of_orders):
        order = Order(
            order_id=i + 1,
            price=10_000,
            quantity=1,
            side=Side.BUY if i % 2 == 0 else Side.SELL,
        )

        order_start = time.perf_counter_ns()
        book.add_order(order)
        latencies_ns.append(time.perf_counter_ns() - order_start)

    elapsed_ns = time.perf_counter_ns() - start

    sorted_latencies = sorted(latencies_ns)
    p99_index = min(
        len(sorted_latencies) - 1,
        int(len(sorted_latencies) * 0.99),
    )

    print("ChronosMatch Order Book Benchmark")
    print("-" * 40)
    print(f"Orders processed: {number_of_orders:,}")
    print(f"Elapsed time: {elapsed_ns / 1e9:.4f} seconds")
    print(f"Throughput: {number_of_orders / (elapsed_ns / 1e9):,.0f} orders/sec")
    print(f"Mean latency: {statistics.mean(latencies_ns):,.0f} ns")
    print(f"P99 latency: {sorted_latencies[p99_index]:,.0f} ns")
    print(f"Trades recorded: {len(book.trades):,}")


if __name__ == "__main__":
    run_benchmark()
