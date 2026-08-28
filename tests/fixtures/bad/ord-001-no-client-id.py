# BAD: order create without a stable client id
def create_order(ticker, side, count, price):
    return post("/margin/orders", {"ticker": ticker, "side": side, "count": count, "price": price})
