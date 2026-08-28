# GOOD: state-changing call gated behind explicit write flag
import requests
if write_enabled and user_authorized:
    requests.delete("https://external-api.kalshi.com/trade-api/v2/margin/orders")
