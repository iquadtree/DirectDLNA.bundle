# -*- coding: utf-8 -*-
"""
    Some quirks for Plex Media Server framework runtime environment
    Copyright: 2025, John Doe
    License: MIT
"""

# Return True if all elements of the iterable are true (or if the iterable is empty)
def all(iterable):
    for element in iterable:
        if not element:
            return False
    return True

# Return True if any element of the iterable is true. If the iterable is empty, return False.
def any(iterable):
    for element in iterable:
        if element:
            return True
    return False
