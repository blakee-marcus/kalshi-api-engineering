# BAD: signs a margin REST request but the path omits /margin
import time, base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def sign(method, path, key):
    ts = str(int(time.time() * 1000))
    msg = f"{ts}{method}{path}"
    # path passed in is "/trade-api/v2/portfolio/balance" (no /margin)
    return base64.b64encode(b"x").decode()

# Perps balance call — but path lacks /margin => every margin private call 401s
r = sign("GET", "/trade-api/v2/portfolio/balance", "key")
