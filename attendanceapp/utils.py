import re


def validate_query_param(param_value):
    """
    Validate a query parameter to allow only alphabets and numbers.
    Returns True if valid, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9]*$'  
    return bool(re.match(pattern, param_value))