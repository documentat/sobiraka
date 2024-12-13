from dataclasses import dataclass

from sobiraka.utils import RelativePath


@dataclass(kw_only=True, frozen=True)
class Config_Prover_Checks:
    """Boolean options representing enabled and disabled checks that should be performed."""

    phrases_must_begin_with_capitals: bool = False
    """
    For each phrase in the text, check that its first character is a lowercase letter, unless:
    
    - the phrase is inside a code span or a code block,
    - the phrase is an item's first phrase in a list that is preceded by a colon.
    """


@dataclass(kw_only=True, frozen=True)
class Config_Prover:
    """Settings related to :class:`.Prover`."""

    dictionaries: tuple[str, ...] = ()
    """
    The Hunspell dictionaries to use for spellchecking.
    
    This may include both the names of the dictionaries available in the environment (e.g., ``en_US``)
    and relative paths to specific dictionaries present under the project root.
    """

    exceptions: tuple[RelativePath, ...] = ()
    """
    Relative paths to the files containing word and phrases that should not be treated as incorrect.
    
    See :func:`.exceptions_regexp()`.
    """

    checks: Config_Prover_Checks = Config_Prover_Checks()
    """Additional checks enabled for this volume."""
