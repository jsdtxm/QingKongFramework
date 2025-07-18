import re


def username_validator(v):
    if v and not re.match(r"^[a-zA-Z0-9_]{3,20}$", v):
        raise ValueError(
            "Invalid username format. Username must be 3-20 characters long and can only contain letters, numbers, and underscores."
        )
    return v


def email_validator(v):
    if v and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
        raise ValueError("Invalid email format")
    return v


def password_validator(password: str):
    """
    Validate the format of a password.
    """

    if not password:
        raise ValueError("Password cannot be empty.")

    # 密码复杂度规则：
    # 1. 至少8个字符
    # 2. 至少包含一个大写字母
    # 3. 至少包含一个小写字母
    # 4. 至少包含一个数字
    # 5. 至少包含一个特殊字符（如 !@#$%^&*()-_=+[]{}|;:'",.<>/?）
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()\-_=+$${}|;:'\",.<>/?]", password):
        raise ValueError("Password must contain at least one special character.")

    return password
