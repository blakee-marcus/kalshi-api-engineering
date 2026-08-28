# BAD: binary float for money
def total(price, qty):
    return float(price) * float(qty)  # precision loss on Kalshi money
