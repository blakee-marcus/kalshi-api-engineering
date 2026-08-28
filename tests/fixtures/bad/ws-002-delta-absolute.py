# BAD: delta applied as absolute assignment
levels = {}
def on_delta(price, delta):
    levels[price] = delta  # overwrites the level instead of adjusting it
