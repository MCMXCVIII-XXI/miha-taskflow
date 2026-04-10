def camel_to_snake(input_name: str) -> str:
    """Converts CamelCase strings to snake_case format.

    Utility function for converting CamelCase class and variable names to
    snake_case format used for database table and column names. Handles
    consecutive uppercase letters and acronyms appropriately.

    Args:
        input_name (str): CamelCase string to convert

    Returns:
        str: Converted snake_case string

    Examples:
        >>> camel_to_snake('userName')
        'user_name'
        >>> camel_to_snake('HTTPResponseCode')
        'http_response_code'
        >>> camel_to_snake('SDKDemo')
        'sdk_demo'
        >>> camel_to_snake('UserProfile')
        'user_profile'
    """
    chars = []

    for c_idx, char in enumerate(input_name):
        if c_idx and char.isupper():
            nxt_idx = c_idx + 1
            flag = nxt_idx >= len(input_name) or input_name[nxt_idx].isupper()
            prev_char = input_name[c_idx - 1]
            if prev_char.isupper() and flag:
                pass
            else:
                chars.append("_")
        chars.append(char.lower())
    return "".join(chars)
