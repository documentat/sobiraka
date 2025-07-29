from dataclasses import dataclass, field

from utilspie.collectionsutils import frozendict


@dataclass(kw_only=True, frozen=True)
class Config_Content:
    """Format-agnostic content settings."""

    numeration: bool = False
    """Whether to add automatic numbers to all the headers."""

    emoji_replacements: dict[str, str] = field(default_factory=frozendict)
