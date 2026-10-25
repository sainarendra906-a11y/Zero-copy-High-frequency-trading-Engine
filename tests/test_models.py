
import unittest

from src.models import Order, Side, ORDER_STRUCT


class TestOrder(unittest.TestCase):
    def test_binary_round_trip(self):
        order = Order(1, 10000, 5, Side.BUY)
        restored = Order.from_bytes(order.to_bytes())

        self.assertEqual(restored, order)

    def test_binary_size(self):
        order = Order(1, 10000, 5, Side.BUY)

        self.assertEqual(len(order.to_bytes()), ORDER_STRUCT.size)
        self.assertEqual(ORDER_STRUCT.size, 21)

    def test_sell_order(self):
        order = Order(2, 10500, 3, Side.SELL)

        self.assertEqual(order.side, Side.SELL)
        self.assertEqual(Order.from_bytes(order.to_bytes()), order)

    def test_invalid_price(self):
        with self.assertRaises(ValueError):
            Order(1, 0, 5, Side.BUY)

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            Order(1, 10000, 0, Side.BUY)

    def test_invalid_binary_size(self):
        with self.assertRaises(ValueError):
            Order.from_bytes(b"bad")


    def test_invalid_binary_side(self):
        invalid_data = ORDER_STRUCT.pack(1, 10000, 5, 99)

        with self.assertRaisesRegex(ValueError, "Invalid order side"):
            Order.from_bytes(invalid_data)

if __name__ == "__main__":
    unittest.main()
