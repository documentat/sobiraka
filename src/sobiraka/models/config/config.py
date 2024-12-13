from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from utilspie.collectionsutils import frozendict

from .config_content import Config_Content
from .config_latex import Config_Latex
from .config_paths import Config_Paths
from .config_pdf import Config_PDF
from .config_prover import Config_Prover
from .config_web import Config_Web


@dataclass(kw_only=True, frozen=True)
class Config:
    """
    Configuration for a volume. Used as a base class for :obj:`.Volume`.
    """
    # pylint: disable=too-many-instance-attributes

    title: str = None

    paths: Config_Paths = field(default_factory=Config_Paths, kw_only=True)
    """Settings that affect discovering source files."""

    web: Config_Web = field(default_factory=Config_Web, kw_only=True)
    """Settings related to :class:`.WebBuilder`."""

    content: Config_Content = field(default=Config_Content, kw_only=True)

    latex: Config_Latex = field(default_factory=Config_Latex, kw_only=True)
    """Settings related to :class:`.LatexBuilder`."""

    pdf: Config_PDF = field(default=Config_PDF, kw_only=True)
    """Settings related to :class:`.WeasyBuilder`."""

    prover: Config_Prover = field(default_factory=Config_Prover, kw_only=True)
    """Settings related to :class:`.Prover`."""

    variables: dict[str, Any] = field(default_factory=frozendict, kw_only=True)
    """Arbitrary variables that can be passed to the template engine."""
