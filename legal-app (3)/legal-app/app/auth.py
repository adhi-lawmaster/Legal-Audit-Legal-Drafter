"""Autentikasi tanpa dependensi tambahan: scrypt untuk password, JWT HS256 (stdlib)."""
import base64, hashlib, hmac, json, os, time

def _key() -> bytes:
    k = os.getenv("SECRET_KEY", "")
    if len(k) < 16:
        raise RuntimeError("SECRET_KEY wajib diisi (minimal 16 karakter).")
    return k.encode()

def ensure_secret(): _key()

def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    return salt.hex() + "$" + hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1).hex()

def verify_password(pw: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$")
        c = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()
        return hmac.compare_digest(c, h)
    except Exception:
        return False

_b = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
_ub = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def make_token(sub: int, role: str, ttl: int = 8 * 3600) -> str:
    head = _b(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b(json.dumps({"sub": sub, "role": role, "exp": int(time.time()) + ttl}).encode())
    sig = _b(hmac.new(_key(), f"{head}.{body}".encode(), hashlib.sha256).digest())
    return f"{head}.{body}.{sig}"

def read_token(t: str) -> dict:
    try:
        head, body, sig = t.split(".")
        good = _b(hmac.new(_key(), f"{head}.{body}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, good):
            raise ValueError("tanda tangan salah")
        claims = json.loads(_ub(body))
        if claims["exp"] < time.time():
            raise ValueError("token kedaluwarsa")
        return claims
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise ValueError(str(e))
