from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class Config_Content:
    """Format-agnostic content settings."""

    numeration: bool = False
    """Whether to add automatic numbers to all the headers."""
