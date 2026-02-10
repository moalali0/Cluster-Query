import hashlib
import math
import re

EMBEDDING_DIM = 384
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _hash_token(token: str) -> tuple[int, int]:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    idx = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
    sign = 1 if digest[4] % 2 == 0 else -1
    return idx, sign


def embed_text(text: str) -> list[float]:
    vec = [0.0] * EMBEDDING_DIM
    tokens = _tokenize(text)
    if not tokens:
        return vec

    for token in tokens:
        idx, sign = _hash_token(token)
        vec[idx] += float(sign)

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def to_pgvector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"
