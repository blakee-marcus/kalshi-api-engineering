# GOOD: perps uses margin REST for lifecycle/position state
subs = ["user_orders", "fill"]
def lifecycle_state():
    return get("/margin/positions")
