import re


def validate_query_param(param_value):
    """
    Validate a query parameter to allow only alphabets and numbers.
    Returns True if valid, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9]*$'  
    return bool(re.match(pattern, param_value))


def to_bool(value, default=True):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return default