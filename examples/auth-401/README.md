# Broken authentication — the classic margin 401 trap

Public endpoints return `200`; private endpoints return `401`. The developer
concludes "bad credentials." The real cause: the margin REST request is signed
over `/trade-api/v2/...` but the margin path segment `/margin` was dropped from
the signed message, so Kalshi rejects the signature on every private call.

## broken.py
```python
import time, base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def sign(method, path, key_path, body=None):
    ts = str(int(time.time() * 1000))
    # BUG: path passed in is "/trade-api/v2/portfolio/balance" (no /margin)
    msg = f"{ts}{method}{path.split('?')[0]}"
    if body: msg += body
    key = serialization.load_pem_private_key(open(key_path, "rb").read(), password=None)
    sig = key.sign(msg.encode(), padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                  salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return {"KALSHI-ACCESS-KEY": "YOUR_KEY_ID",
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
            "KALSHI-ACCESS-TIMESTAMP": ts}

# Perps balance call — but path lacks /margin => every margin private call 401s
r = sign("GET", "/trade-api/v2/portfolio/balance", "private_key.pem")
```

Run the checker:
```bash
python ../../scripts/kalshi_doctor.py broken.py
# [FAIL] KALSHI-AUTH-001  broken.py:11
#        Margin request signing must cover the full /trade-api/v2/margin/... path.
```

## fixed.py
```python
import time, base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def sign(method, path, key_path, body=None):
    ts = str(int(time.time() * 1000))
    if not path.startswith("/trade-api/v2"):
        path = f"/trade-api/v2{path}"
    # FIX: sign over the full /trade-api/v2/margin/... path for margin calls
    msg = f"{ts}{method}{path.split('?')[0]}"
    if body: msg += body
    key = serialization.load_pem_private_key(open(key_path, "rb").read(), password=None)
    sig = key.sign(msg.encode(), padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                  salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return {"KALSHI-ACCESS-KEY": "YOUR_KEY_ID",
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
            "KALSHI-ACCESS-TIMESTAMP": ts}

r = sign("GET", "/margin/portfolio/balance", "private_key.pem")  # => 200
```

Source: https://docs.kalshi.com/perps_openapi.yaml
