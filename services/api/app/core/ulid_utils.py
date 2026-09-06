import os
import time

CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_ulid() -> str:
    """
    Generates a 26-character Crockford Base32 ULID.
    Attempts to import ULID from python-ulid first; falls back to pure-Python generation.
    """
    try:
        from ulid import ULID
        return str(ULID())
    except ImportError:
        # 48-bit timestamp (epoch ms)
        t = int(time.time() * 1000)
        time_chars = []
        for _ in range(10):
            time_chars.append(CROCKFORD_BASE32[t & 0x1F])
            t >>= 5
        time_part = "".join(reversed(time_chars))

        # 80-bit randomness (16 chars * 5 bits)
        random_bytes = os.urandom(10)
        rand_int = int.from_bytes(random_bytes, byteorder="big")
        rand_chars = []
        for _ in range(16):
            rand_chars.append(CROCKFORD_BASE32[rand_int & 0x1F])
            rand_int >>= 5
        rand_part = "".join(reversed(rand_chars))

        return time_part + rand_part
