
import unittest

from src.models import Order, Side
from src.order_book import OrderBook


class TestOrderBook(unittest.TestCase):
    def setUp(self):
        self.book = OrderBook()

    def test_orders_match(self):
        self.book.add_order(Order(1, 10000, 5, Side.BUY))
        trades = self.book.add_order(
            Order(2, 9900, 3, Side.SELL)
        )

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].price, 10000)
        self.assertEqual(trades[0].quantity, 3)
        self.assertEqual(self.book.best_bid().quantity, 2)
        self.assertIsNone(self.book.best_ask())

    def test_non_crossing_orders_remain_open(self):
        self.book.add_order(Order(1, 9900, 5, Side.BUY))
        trades = self.book.add_order(
            Order(2, 10100, 3, Side.SELL)
        )

        self.assertEqual(trades, [])
        self.assertEqual(self.book.best_bid().price, 9900)
        self.assertEqual(self.book.best_ask().price, 10100)

    def test_sell_matches_best_bid_first(self):
        self.book.add_order(Order(1, 10000, 2, Side.BUY))
        self.book.add_order(Order(2, 10100, 2, Side.BUY))

        trades = self.book.add_order(
            Order(3, 9900, 1, Side.SELL)
        )

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].buy_order_id, 2)
        self.assertEqual(trades[0].price, 10100)

    def test_one_order_matches_multiple_orders(self):
        self.book.add_order(Order(1, 10000, 2, Side.BUY))
        self.book.add_order(Order(2, 10100, 3, Side.BUY))

        trades = self.book.add_order(
            Order(3, 9900, 4, Side.SELL)
        )

        self.assertEqual(len(trades), 2)
        self.assertEqual(
            sum(trade.quantity for trade in trades), 4
        )
        self.assertEqual(self.book.best_bid().quantity, 1)

    def test_equal_price_preserves_time_priority(self):
        self.book.add_order(Order(1, 10000, 2, Side.BUY))
        self.book.add_order(Order(2, 10000, 3, Side.BUY))

        trades = self.book.add_order(
            Order(3, 10000, 1, Side.SELL)
        )

        self.assertEqual(trades[0].buy_order_id, 1)

    def test_trade_history_is_recorded(self):
        self.book.add_order(Order(1, 10000, 2, Side.BUY))
        self.book.add_order(Order(2, 9900, 2, Side.SELL))

        self.assertEqual(len(self.book.trades), 1)


if __name__ == "__main__":
    unittest.main()



def test_cancel_buy_order():
    book = OrderBook()
    book.add_order(Order(101, 10000, 5, Side.BUY))

    assert book.cancel_order(101) is True
    assert book.best_bid() is None


def test_cancel_sell_order():
    book = OrderBook()
    book.add_order(Order(201, 10100, 5, Side.SELL))

    assert book.cancel_order(201) is True
    assert book.best_ask() is None


def test_cancel_nonexistent_order():
    book = OrderBook()

    assert book.cancel_order(999) is False
def test_buy_order_matches_multiple_asks_at_best_price_first():
    book = OrderBook()

    book.add_order(Order(1, 9900, 2, Side.SELL))
    book.add_order(Order(2, 10000, 3, Side.SELL))

    trades = book.add_order(
        Order(3, 10000, 4, Side.BUY)
    )

    assert len(trades) == 2

    assert trades[0].sell_order_id == 1
    assert trades[0].price == 9900
    assert trades[0].quantity == 2

    assert trades[1].sell_order_id == 2
    assert trades[1].price == 10000
    assert trades[1].quantity == 2

    assert book.best_ask().order_id == 2
    assert book.best_ask().quantity == 1
    assert book.best_bid() is None


def test_cancel_partially_filled_buy_order():
    book = OrderBook()

    book.add_order(Order(101, 10000, 5, Side.BUY))
    book.add_order(Order(102, 9900, 3, Side.SELL))

    # Two units of the buy order should remain.
    assert book.best_bid().quantity == 2

    # Cancel the remaining quantity.
    assert book.cancel_order(101) is True
    assert book.best_bid() is None