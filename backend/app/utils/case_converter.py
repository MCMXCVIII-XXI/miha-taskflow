def camel_to_snake(input_name: str) -> str:
    """
    >>> camel_to_snake('userName')
    'user_name'
    >>> camel_to_snake('HTTPResponseCode')
    'http_response_code'
    >>> camel_to_snake('SDKDemo')
    'sdk_demo'
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
