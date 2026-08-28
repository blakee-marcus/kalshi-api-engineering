# GOOD: perps uses /positions REST + private user_orders stream
subs = ["user_orders", "fill"]
def positions():
    return get("/margin/positions")
