"""
Nostr protocol utilities for Buzz Hive Mind Relay.
Includes BIP-340 Schnorr signature, NIP-01 canonical serialization,
key generation, and NIP-42 authentication event creation.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple

# Curve constants for secp256k1
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_G = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
)


def _point_add(p1: Optional[Tuple[int, int]], p2: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and y1 != y2:
        return None
    if x1 == x2:
        m = (3 * x1 * x1 * pow(2 * y1, _p - 2, _p)) % _p
    else:
        m = ((y2 - y1) * pow(x2 - x1, _p - 2, _p)) % _p
    x3 = (m * m - x1 - x2) % _p
    y3 = (m * (x1 - x3) - y1) % _p
    return x3, y3


def _point_mul(p: Optional[Tuple[int, int]], d: int) -> Optional[Tuple[int, int]]:
    res = None
    curr = p
    while d > 0:
        if d & 1:
            res = _point_add(res, curr)
        curr = _point_add(curr, curr)
        d >>= 1
    return res


def _tagged_hash(tag: str, data: bytes) -> bytes:
    tag_hash = hashlib.sha256(tag.encode("utf-8")).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


def generate_keypair() -> Tuple[str, str]:
    """Generates a random secp256k1 private key and its x-only public key in hex."""
    while True:
        priv_int = secrets.randbits(256)
        if 1 <= priv_int < _n:
            break
    pub_point = _point_mul(_G, priv_int)
    assert pub_point is not None
    # Negate private key if y is odd (BIP-340)
    if pub_point[1] % 2 != 0:
        priv_int = _n - priv_int
    priv_hex = f"{priv_int:064x}"
    pub_hex = f"{pub_point[0]:064x}"
    return priv_hex, pub_hex


def get_pubkey_from_privkey(priv_hex: str) -> str:
    """Derives the BIP-340 32-byte public key (hex) from a private key (hex)."""
    priv_int = int(priv_hex, 16)
    pub_point = _point_mul(_G, priv_int)
    assert pub_point is not None
    return f"{pub_point[0]:064x}"


def schnorr_sign(msg: bytes, priv_hex: str) -> str:
    """Computes a BIP-340 Schnorr signature over msg (32-byte digest)."""
    d0 = int(priv_hex, 16)
    P = _point_mul(_G, d0)
    assert P is not None
    if P[1] % 2 != 0:
        d = _n - d0
    else:
        d = d0

    t = d.to_bytes(32, "big")
    rand_aux = secrets.token_bytes(32)
    k0 = int.from_bytes(_tagged_hash("BIP0340/aux", rand_aux), "big") ^ d
    k_prime = int.from_bytes(
        _tagged_hash("BIP0340/nonce", t + P[0].to_bytes(32, "big") + msg), "big"
    ) % _n
    if k_prime == 0:
        k_prime = 1
    R = _point_mul(_G, k_prime)
    assert R is not None
    if R[1] % 2 != 0:
        k = _n - k_prime
    else:
        k = k_prime

    e = int.from_bytes(
        _tagged_hash("BIP0340/challenge", R[0].to_bytes(32, "big") + P[0].to_bytes(32, "big") + msg),
        "big",
    ) % _n
    s = (k + e * d) % _n
    sig_bytes = R[0].to_bytes(32, "big") + s.to_bytes(32, "big")
    return sig_bytes.hex()


def serialize_event(pubkey: str, created_at: int, kind: int, tags: List[List[str]], content: str) -> str:
    """Produces the exact NIP-01 canonical JSON serialization."""
    return json.dumps(
        [0, pubkey, created_at, kind, tags, content],
        separators=(",", ":"),
        ensure_ascii=False,
    )


def create_event(
    priv_hex: str,
    kind: int,
    content: str,
    tags: Optional[List[List[str]]] = None,
    created_at: Optional[int] = None,
) -> Dict[str, Any]:
    """Builds, computes ID hash, and signs a Nostr event."""
    if tags is None:
        tags = []
    if created_at is None:
        created_at = int(time.time())

    pubkey = get_pubkey_from_privkey(priv_hex)
    serialized = serialize_event(pubkey, created_at, kind, tags, content)
    event_id = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    sig = schnorr_sign(bytes.fromhex(event_id), priv_hex)

    return {
        "id": event_id,
        "pubkey": pubkey,
        "created_at": created_at,
        "kind": kind,
        "tags": tags,
        "content": content,
        "sig": sig,
    }


def create_auth_event(priv_hex: str, challenge: str, relay_url: str) -> Dict[str, Any]:
    """Creates a NIP-42 authentication event (Kind 22242)."""
    tags = [
        ["relay", relay_url],
        ["challenge", challenge],
    ]
    return create_event(
        priv_hex=priv_hex,
        kind=22242,
        content="",
        tags=tags,
    )


# Common Nostr / Buzz Kinds
KIND_METADATA = 0
KIND_TEXT_NOTE = 1
KIND_REACTION = 7
KIND_STREAM_MESSAGE = 9
KIND_PRESENCE = 20001
KIND_AUTH = 22242
KIND_JOB_REQUEST = 43001
KIND_JOB_RESULT = 43002
KIND_FORUM_POST = 45001
KIND_FORUM_COMMENT = 45003
KIND_WORKFLOW_EVENT = 46001
