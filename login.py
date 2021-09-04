import hashlib
import os
from typing import Tuple

HASH_ALGORITHM = 'sha256'
ENCODING = 'utf-8'
DIGEST_SIZE = 32
ITERATION = 100_000


def hash(password: str, salt_str: str = None) -> Tuple[str, str]:
    if salt_str is None:
        salt = os.urandom(DIGEST_SIZE)
    else:
        salt = bytes.fromhex(salt_str)

    key = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode(ENCODING),
        salt,
        ITERATION,
        dklen=DIGEST_SIZE
    )
    return key.hex(), salt.hex()
