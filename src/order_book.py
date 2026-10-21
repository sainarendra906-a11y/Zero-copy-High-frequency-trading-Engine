
from dataclasses import dataclass
from typing import Optional

from src.models import Order, Side


@dataclass(frozen=True, slots=True)
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: int
    quantity: int


class OrderBook:
    """Single-instrument order book using price-time priority."""

    def __init__(self):
        self.bids: list[Order] = []
        self.asks: list[Order] = []
        self.trades: list[Trade] = []

    def add_order(self, order: Order) -> list[Trade]:
        if order.side == Side.BUY:
            return self._match_buy(order)
        return self._match_sell(order)

    def _match_buy(self, order: Order) -> list[Trade]:
        new_trades = []
        remaining = order.quantity

        while remaining > 0 and self.asks:
            best_ask = min(self.asks, key=lambda o: o.price)

            if order.price < best_ask.price:
                break

            quantity = min(remaining, best_ask.quantity)
            new_trades.append(
                Trade(order.order_id, best_ask.order_id,
                      best_ask.price, quantity)
            )

            remaining -= quantity
            self.asks.remove(best_ask)

            if best_ask.quantity > quantity:
                self.asks.append(
                    Order(best_ask.order_id, best_ask.price,
                          best_ask.quantity - quantity, Side.SELL)
                )

        if remaining > 0:
            self.bids.append(
                Order(order.order_id, order.price, remaining, Side.BUY)
            )

        self._sort_book()
        self.trades.extend(new_trades)
        return new_trades

    def _match_sell(self, order: Order) -> list[Trade]:
        new_trades = []
        remaining = order.quantity

        while remaining > 0 and self.bids:
            best_bid = max(self.bids, key=lambda o: o.price)

            if order.price > best_bid.price:
                break

            quantity = min(remaining, best_bid.quantity)
            new_trades.append(
                Trade(best_bid.order_id, order.order_id,
                      best_bid.price, quantity)
            )

            remaining -= quantity
            self.bids.remove(best_bid)

            if best_bid.quantity > quantity:
                self.bids.append(
                    Order(best_bid.order_id, best_bid.price,
                          best_bid.quantity - quantity, Side.BUY)
                )

        if remaining > 0:
            self.asks.append(
                Order(order.order_id, order.price, remaining, Side.SELL)
            )

        self._sort_book()
        self.trades.extend(new_trades)
        return new_trades

    def _sort_book(self) -> None:
        # Stable sorting preserves arrival order for equal prices.
        self.bids.sort(key=lambda o: o.price, reverse=True)
        self.asks.sort(key=lambda o: o.price)

    def best_bid(self) -> Optional[Order]:
        return self.bids[0] if self.bids else None

    def best_ask(self) -> Optional[Order]:
        return self.asks[0] if self.asks else None


    def cancel_order(self, order_id: int) -> bool:
        """Cancel a resting order by ID. Return True if found."""
        for book_side in (self.bids, self.asks):
            for index, order in enumerate(book_side):
                if order.order_id == order_id:
                    book_side.pop(index)
                    return True

        return False
