
from src.models import Order, Side
from src.order_book import OrderBook


def main():
    book = OrderBook()

    print("ChronosMatch Trading Engine")
    print("-" * 35)

    # Add a resting sell order at price 100.
    sell_order = Order(
        order_id=1,
        price=100,
        quantity=5,
        side=Side.SELL,
    )
    book.add_order(sell_order)

    print("Sell order added: 5 units at price 100")

    # Submit a buy order that crosses the sell price.
    buy_order = Order(
        order_id=2,
        price=100,
        quantity=3,
        side=Side.BUY,
    )
    trades = book.add_order(buy_order)

    for trade in trades:
        print(
            f"TRADE: Buy #{trade.buy_order_id} / "
            f"Sell #{trade.sell_order_id} | "
            f"Price: {trade.price} | "
            f"Quantity: {trade.quantity}"
        )

    best_ask = book.best_ask()
    print(f"Remaining sell quantity: {best_ask.quantity if best_ask else 0}")
    print("Engine verification completed.")


if __name__ == "__main__":
    main()
