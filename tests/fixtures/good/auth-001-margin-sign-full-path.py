# GOOD: signs the full /trade-api/v2/margin/... path for margin REST
import time, base64

def sign(method, path, key):
    ts = str(int(time.time() * 1000))
    if not path.startswith("/trade-api/v2/margin"):
        path = f"/trade-api/v2/margin{path}"
    msg = f"{ts}{method}{path}"
    return base64.b64encode(msg.encode()).decode()

r = sign("GET", "/portfolio/balance", "key")
assert r  # signed over /trade-api/v2/margin/portfolio/balance
