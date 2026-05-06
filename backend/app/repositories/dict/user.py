from typing import TypedDict


class UserIlike(TypedDict, total=False):
    """TypedDict for ilike queries in UserRepository.

    Allows using patterns for searching string fields.
    Used in find_many() and get() methods.

    Example usage:
        await UserRepository.find_many(
            session,
            ilike={"username": "%admin%", "email": "%@test.com%"}
        )
    """

    username: str
    email: str
    first_name: str
    last_name: str
    patronymic: str
