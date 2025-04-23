class _Missing:
    def __repr__(self):
        return 'MISSING'

    def __bool__(self):
        raise ValueError


MISSING = _Missing()
"""
A special value that represents a field that is expected to be filled alter.
It is intentionally not True, not False, and not iterable, to help prevent accidental usage.
"""
