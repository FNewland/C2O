"""Test-only IAP signing: an ES256 key pair, its JWK set and signed
assertions shaped like the ones Google IAP puts in X-Goog-IAP-JWT-Assertion.
Never used outside tests (and the Playwright header-injecting proxy)."""
from __future__ import annotations

import json
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from smo_common.web.iap_jwt import ISSUER, b64url

AUD_OPS = "/projects/123456789/global/backendServices/1111111111111111111"
AUD_SIM = "/projects/123456789/global/backendServices/2222222222222222222"


class FakeIap:
    def __init__(self, kid: str = "test-kid-1"):
        self.kid = kid
        self.key = ec.generate_private_key(ec.SECP256R1())

    def jwk(self) -> dict:
        n = self.key.public_key().public_numbers()
        return {"kty": "EC", "crv": "P-256", "alg": "ES256", "use": "sig", "kid": self.kid,
                "x": b64url(n.x.to_bytes(32, "big")), "y": b64url(n.y.to_bytes(32, "big"))}

    def jwks(self) -> dict:
        return {"keys": [self.jwk()]}

    def token(self, email: str, *, aud: str = AUD_OPS, iss: str = ISSUER,
              iat: float | None = None, exp: float | None = None, kid: str | None = None,
              alg: str = "ES256", extra: dict | None = None) -> str:
        now = time.time()
        iat = now - 5 if iat is None else iat
        exp = iat + 600 if exp is None else exp
        header = {"alg": alg, "kid": kid or self.kid, "typ": "JWT"}
        claims = {"iss": iss, "aud": aud, "iat": int(iat), "exp": int(exp),
                  "sub": "accounts.google.com:1234", "email": email, "hd": "c2o.live",
                  **(extra or {})}
        msg = (b64url(json.dumps(header).encode()) + "." +
               b64url(json.dumps(claims).encode()))
        r, s = decode_dss_signature(self.key.sign(msg.encode(), ec.ECDSA(hashes.SHA256())))
        return msg + "." + b64url(r.to_bytes(32, "big") + s.to_bytes(32, "big"))

    def headers(self, email: str, **kw) -> dict:
        return {"X-Goog-Authenticated-User-Email": f"accounts.google.com:{email}",
                "X-Goog-IAP-JWT-Assertion": self.token(email, **kw)}
