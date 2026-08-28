# BAD: state-changing prod call with no execution boundary
import requests
requests.delete("https://external-api.kalshi.com/trade-api/v2/margin/orders")
