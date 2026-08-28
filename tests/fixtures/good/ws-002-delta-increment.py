# GOOD: delta applied as increment
levels = {}
def on_delta(price, delta):
    levels[price] = levels.get(price, 0) + delta
    if levels[price] == 0:
        levels.pop(price, None)
