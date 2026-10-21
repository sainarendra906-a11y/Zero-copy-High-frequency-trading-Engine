
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
