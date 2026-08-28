# GOOD: perps WS auths on its own path
WS_URL = "wss://external-api-margin-ws.kalshi.com/trade-api/ws/v2/margin"
def auth_perps():
    return sign("GET", "/trade-api/ws/v2/margin", key)
