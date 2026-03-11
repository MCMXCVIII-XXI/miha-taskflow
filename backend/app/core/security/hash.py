from argon2 import PasswordHasher, exceptions
from argon2.low_level import Type

password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_hasher.verify(hashed_password, plain_password)
        return True
    except (exceptions.VerifyMismatchError, exceptions.InvalidHashError):
        return False
