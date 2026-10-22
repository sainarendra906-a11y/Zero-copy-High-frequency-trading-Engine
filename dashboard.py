
import os
import time

from src.order_book import OrderBook
from src.models import Order, Side


def display_dashboard(book, processed):
    os.system("cls" if os.name == "nt" else "clear")

    best_bid = book.best_bid()
    best_ask = book.best_ask()

    spread = (
        best_ask.price - best_bid.price
        if best_bid is not None and best_ask is not None
        else None
    )

    print("=" * 48)
    print("       CHRONOSMATCH TRADING DASHBOARD")
    print("=" * 48)
    print(f"Orders processed : {processed}")
    print(f"Trades executed  : {len(book.trades)}")
    print("-" * 48)

    print("BEST BID (BUY)")
    if best_bid:
        print(f"Price: {best_bid.price} | Quantity: {best_bid.quantity}")
    else:
        print("No buy orders")

    print("-" * 48)
    print("BEST ASK (SELL)")
    if best_ask:
        print(f"Price: {best_ask.price} | Quantity: {best_ask.quantity}")
    else:
        print("No sell orders")

    print("-" * 48)
    print(f"MARKET SPREAD: {spread if spread is not None else 'N/A'}")
    print("=" * 48)

    if book.trades:
        latest = book.trades[-1]
        print(
            f"Latest trade: Buy #{latest.buy_order_id} / "
            f"Sell #{latest.sell_order_id} | "
            f"Price: {latest.price} | Quantity: {latest.quantity}"
        )


def main():
    book = OrderBook()
    processed = 0

    sample_orders = [
        Order(1, 100, 5, Side.SELL),
        Order(2, 98, 4, Side.BUY),
        Order(3, 99, 3, Side.BUY),
        Order(4, 99, 2, Side.SELL),
        Order(5, 100, 2, Side.BUY),
    ]

    for order in sample_orders:
        book.add_order(order)
        processed += 1
        display_dashboard(book, processed)
        time.sleep(1)

    print("\nDashboard demo complete.")


if __name__ == "__main__":
    main()
