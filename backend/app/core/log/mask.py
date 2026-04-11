def _mask_email(email: str) -> str:
    """Mask email for logging: user@example.com → u***@example.com."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"
