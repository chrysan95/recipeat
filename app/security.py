"""Password hashing (bcrypt) and password policy."""
import bcrypt
from flask import current_app

_DUMMY = None


def _rounds():
    try:
        return current_app.config["BCRYPT_ROUNDS"]
    except RuntimeError:
        return 12


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=_rounds())).decode("ascii")


def verify_password(password, hashed):
    """Constant-ish time: compares against a dummy hash when the user doesn't exist."""
    global _DUMMY
    if not hashed:
        if _DUMMY is None:
            _DUMMY = hash_password("timing-equaliser")
        hashed = _DUMMY
        bcrypt.checkpw((password or "").encode("utf-8")[:72], hashed.encode("ascii"))
        return False
    return bcrypt.checkpw((password or "").encode("utf-8")[:72], hashed.encode("ascii"))


def validate_password(pw):
    if not isinstance(pw, str) or len(pw) < 8:
        return "Kata sandi minimal 8 karakter."
    if len(pw.encode("utf-8")) > 72:
        return "Kata sandi maksimal 72 karakter."
    if not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw):
        return "Kata sandi harus berisi huruf dan angka."
    return None
