# BAD: perps WS uses the predictions auth path
WS_URL = "wss://external-api-ws.kalshi.com/trade-api/ws/v2"  # predictions path
def auth_perps():
    return sign("GET", "/trade-api/ws/v2", key)  # reused for perps => silent auth fail
