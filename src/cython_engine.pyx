
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

cdef class CythonOrderBook:
    cdef dict bids
    cdef dict asks
    cdef list trades

    def __cinit__(self):
        self.bids = {}
        self.asks = {}
        self.trades = []

    cpdef list add_order(self, long long order_id,
                         long long price, int quantity, int side):
        cdef list new_trades = []
        cdef long long resting_id
        cdef int resting_qty
        cdef int matched_qty

        if order_id < 0 or price <= 0 or quantity <= 0:
            raise ValueError("Invalid order values")

        if side == 1:  # BUY
            while quantity > 0 and self.asks:
                best_price = min(self.asks)

                if price < best_price:
                    break

                resting_id, resting_qty = self.asks[best_price][0]
                matched_qty = min(quantity, resting_qty)

                trade = (order_id, resting_id, best_price, matched_qty)
                new_trades.append(trade)
                self.trades.append(trade)
                quantity -= matched_qty

                if matched_qty == resting_qty:
                    self.asks[best_price].pop(0)
                    if not self.asks[best_price]:
                        del self.asks[best_price]
                else:
                    self.asks[best_price][0] = (
                        resting_id, resting_qty - matched_qty
                    )

            if quantity > 0:
                self.bids.setdefault(price, []).append((order_id, quantity))

        elif side == 2:  # SELL
            while quantity > 0 and self.bids:
                best_price = max(self.bids)

                if price > best_price:
                    break

                resting_id, resting_qty = self.bids[best_price][0]
                matched_qty = min(quantity, resting_qty)

                trade = (resting_id, order_id, best_price, matched_qty)
                new_trades.append(trade)
                self.trades.append(trade)
                quantity -= matched_qty

                if matched_qty == resting_qty:
                    self.bids[best_price].pop(0)
                    if not self.bids[best_price]:
                        del self.bids[best_price]
                else:
                    self.bids[best_price][0] = (
                        resting_id, resting_qty - matched_qty
                    )

            if quantity > 0:
                self.asks.setdefault(price, []).append((order_id, quantity))

        else:
            raise ValueError("side must be 1 (BUY) or 2 (SELL)")

        return new_trades

    cpdef object best_bid(self):
        if not self.bids:
            return None
        price = max(self.bids)
        order_id, quantity = self.bids[price][0]
        return (order_id, price, quantity)

    cpdef object best_ask(self):
        if not self.asks:
            return None
        price = min(self.asks)
        order_id, quantity = self.asks[price][0]
        return (order_id, price, quantity)
