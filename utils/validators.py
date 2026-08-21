"""
Simple server-side input validation helpers.
"""
import re

EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def is_valid_email(email):
    return bool(email) and bool(EMAIL_REGEX.match(email.strip()))


def is_valid_password(password):
    """At least 6 characters."""
    return bool(password) and len(password) >= 6


def is_valid_name(name):
    return bool(name) and len(name.strip()) >= 2
