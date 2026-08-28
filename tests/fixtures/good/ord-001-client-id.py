# GOOD: create_order carries stable client_order_id
def create_order(ticker, side, count, price, client_order_id):
    return post("/margin/orders", {"ticker": ticker, "side": side, "count": count,
                                    "price": price, "client_order_id": client_order_id})
