import hashlib
import struct

import zstd

BASE_KEY = "Rk3nwA8ZYV0yV"
KEY_LEN = 131
MAGIC = b"mzs\x00"
ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def _init_by_array(seeds: list[int]) -> tuple[list[int], int]:
    n = 624
    mt: list[int] = [0] * n
    mt[0] = 19650218
    for i in range(1, n):
        mt[i] = (1812433253 * (mt[i - 1] ^ (mt[i - 1] >> 30)) + i) & 0xFFFFFFFF
    i, j = 1, 0
    k = max(n, len(seeds))
    for _ in range(k):
        mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525)) + seeds[j] + j) & 0xFFFFFFFF
        i += 1
        j += 1
        if i >= n:
            mt[0] = mt[n - 1]
            i = 1
        if j >= len(seeds):
            j = 0
    for _ in range(n - 1):
        mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1566083941)) - i) & 0xFFFFFFFF
        i += 1
        if i >= n:
            mt[0] = mt[n - 1]
            i = 1
    mt[0] = 0x80000000
    return mt, n


def _twist(mt: list[int], n: int) -> None:
    for i in range(n):
        y = (mt[i] & 0x80000000) | (mt[(i + 1) % n] & 0x7FFFFFFF)
        mt[i] = mt[(i + 397) % n] ^ (y >> 1)
        if y & 1:
            mt[i] ^= 0x9908B0DF


def keystream(seed: str, length: int = KEY_LEN) -> bytes:
    digest = hashlib.md5(seed.encode("utf-8")).digest()
    seeds = list(struct.unpack("<4I", digest))
    mt, n = _init_by_array(seeds)
    out = bytearray()
    idx = n
    while len(out) < 33 * 4:
        if idx >= n:
            _twist(mt, n)
            idx = 0
        y = mt[idx]
        idx += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= y >> 18
        out += struct.pack("<I", y)
    return bytes(out[:length])


def pack_mzs(plain: bytes, filename: str, level: int = 22) -> bytes:
    comp = zstd.compress(plain, level)
    buf = bytearray(MAGIC + struct.pack("<i", len(plain)) + comp)
    ks = keystream(BASE_KEY + filename)
    for i in range(8, len(buf)):
        buf[i] ^= ks[(i - 8) % len(ks)]
    return bytes(buf)


def unpack_mzs(packed: bytes, filename: str) -> bytes:
    if packed[:4] != MAGIC:
        raise ValueError("bad MZS magic")
    (plain_len,) = struct.unpack("<i", packed[4:8])
    buf = bytearray(packed)
    ks = keystream(BASE_KEY + filename)
    for i in range(8, len(buf)):
        buf[i] ^= ks[(i - 8) % len(ks)]
    if bytes(buf[8:12]) != ZSTD_MAGIC:
        raise ValueError("bad ZSTD magic after decrypt")
    plain = zstd.decompress(bytes(buf[8:]))
    if len(plain) != plain_len:
        raise ValueError("length mismatch")
    return plain


def pack_file(data: bytes, filename: str, level: int = 22) -> bytes:
    return pack_mzs(data, filename, level)


def unpack_file(data: bytes, filename: str) -> bytes:
    return unpack_mzs(data, filename)
