"""File-level AES-GCM encryption helpers."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Union

from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DEFAULT_SALT = b"static_salt_change_me"  # placeholder; load from security_meta in real use


def _derive_key(password: str, salt: bytes = DEFAULT_SALT) -> bytes:
    return hash_secret_raw(
        password.encode("utf-8"),
        salt,
        time_cost=3,
        memory_cost=2 ** 15,
        parallelism=1,
        hash_len=32,
        type=Type.ID,
    )


def encrypt_file(src: Union[str, Path], dest: Union[str, Path], password: str) -> None:
    key = _derive_key(password)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    data = Path(src).read_bytes()
    enc = aesgcm.encrypt(nonce, data, None)
    Path(dest).write_bytes(nonce + enc)


def decrypt_file(src: Union[str, Path], dest: Union[str, Path], password: str) -> None:
    key = _derive_key(password)
    aesgcm = AESGCM(key)
    blob = Path(src).read_bytes()
    nonce, ciphertext = blob[:12], blob[12:]
    data = aesgcm.decrypt(nonce, ciphertext, None)
    Path(dest).write_bytes(data)


def secure_delete(path: Union[str, Path]) -> None:
    try:
        p = Path(path)
        if p.exists():
            size = p.stat().st_size
            with open(p, "ba", buffering=0) as f:
                f.seek(0)
                f.write(os.urandom(size))
            p.unlink()
    except FileNotFoundError:
        pass
