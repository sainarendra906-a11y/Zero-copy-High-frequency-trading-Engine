
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

    def test_cancel_buy_order(self):
        self.book.add_order(Order(101, 10000, 5, Side.BUY))

        self.assertTrue(self.book.cancel_order(101))
        self.assertIsNone(self.book.best_bid())

    def test_cancel_sell_order(self):
        self.book.add_order(Order(201, 10100, 5, Side.SELL))

        self.assertTrue(self.book.cancel_order(201))
        self.assertIsNone(self.book.best_ask())

    def test_cancel_nonexistent_order(self):
        self.assertFalse(self.book.cancel_order(999))

    def test_buy_order_matches_multiple_asks_at_best_price_first(self):
        self.book.add_order(Order(1, 9900, 2, Side.SELL))
        self.book.add_order(Order(2, 10000, 3, Side.SELL))

        trades = self.book.add_order(
            Order(3, 10000, 4, Side.BUY)
        )

        self.assertEqual(len(trades), 2)

        self.assertEqual(trades[0].sell_order_id, 1)
        self.assertEqual(trades[0].price, 9900)
        self.assertEqual(trades[0].quantity, 2)

        self.assertEqual(trades[1].sell_order_id, 2)
        self.assertEqual(trades[1].price, 10000)
        self.assertEqual(trades[1].quantity, 2)

        self.assertEqual(self.book.best_ask().order_id, 2)
        self.assertEqual(self.book.best_ask().quantity, 1)
        self.assertIsNone(self.book.best_bid())

    def test_cancel_partially_filled_buy_order(self):
        self.book.add_order(Order(101, 10000, 5, Side.BUY))
        self.book.add_order(Order(102, 9900, 3, Side.SELL))

        self.assertEqual(self.book.best_bid().quantity, 2)
        self.assertTrue(self.book.cancel_order(101))
        self.assertIsNone(self.book.best_bid())

    def test_cancel_one_order_preserves_other_orders(self):
        book = OrderBook()

        first = Order(order_id=201, price=10000, quantity=5, side=Side.BUY)
        second = Order(order_id=202, price=9900, quantity=3, side=Side.BUY)

        book.add_order(first)
        book.add_order(second)

        self.assertTrue(book.cancel_order(201))

        self.assertEqual(len(book.bids), 1)
        self.assertEqual(book.best_bid().order_id, 202)
        self.assertEqual(book.best_bid().quantity, 3)
    def test_cancelling_same_order_twice(self):
        book = OrderBook()

        order = Order(
            order_id=301,
            price=10500,
            quantity=4,
            side=Side.BUY
        )

        book.add_order(order)

        self.assertTrue(book.cancel_order(301))
        self.assertFalse(book.cancel_order(301))
        self.assertIsNone(book.best_bid())
        self.assertEqual(len(book.bids), 0)   
    def test_cancel_partially_filled_sell_order(self):
        book = OrderBook()

        sell = Order(
            order_id=401,
            price=9900,
            quantity=5,
            side=Side.SELL
        )

        buy = Order(
            order_id=402,
            price=10000,
            quantity=3,
            side=Side.BUY
        )

        book.add_order(sell)
        trades = book.add_order(buy)

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 3)

        self.assertIsNotNone(book.best_ask())
        self.assertEqual(book.best_ask().order_id, 401)
        self.assertEqual(book.best_ask().quantity, 2)

        self.assertTrue(book.cancel_order(401))
        self.assertIsNone(book.best_ask())        
if __name__ == "__main__":
    unittest.main()
