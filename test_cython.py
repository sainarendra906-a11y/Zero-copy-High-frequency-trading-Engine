
from src.cython_engine import CythonOrderBook

book = CythonOrderBook()

# Add a SELL order: ID 1, price 100, quantity 5
sell_trades = book.add_order(1, 100, 5, 2)
print("Sell order trades:", sell_trades)

# Add a BUY order: ID 2, price 100, quantity 3
buy_trades = book.add_order(2, 100, 3, 1)
print("Buy order trades:", buy_trades)

print("Best bid:", book.best_bid())
print("Best ask:", book.best_ask())

# Verify the match and remaining quantity
assert sell_trades == []
assert buy_trades == [(2, 1, 100, 3)]
assert book.best_ask() == (1, 100, 2)
assert book.best_bid() is None

print("\nCYTHON ENGINE VERIFICATION PASSED")
