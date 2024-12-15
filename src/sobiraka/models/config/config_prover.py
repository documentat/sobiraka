from dataclasses import dataclass
from typing import Iterable, Self

from panflute import Element

from sobiraka.utils import RelativePath


@dataclass(kw_only=True, frozen=True)
class Config_Prover_Dictionaries:
    hunspell_dictionaries: tuple[str | RelativePath, ...] = ()
    plaintext_dictionaries: tuple[RelativePath, ...] = ()
    regexp_dictionaries: tuple[RelativePath, ...] = ()

    @classmethod
    def load(cls, dictionaries: Iterable[str]) -> Self:
        hunspell_dictionaries = []
        plaintext_dictionaries = []
        regexp_dictionaries = []

        for dic in dictionaries:
            dic_path = RelativePath(dic)
            match dic_path.suffix:
                case '':
                    hunspell_dictionaries.append(dic)
                case '.dic':
                    hunspell_dictionaries.append(dic_path)
                case '.txt':
                    plaintext_dictionaries.append(dic_path)
                case '.regexp':
                    regexp_dictionaries.append(dic_path)
                case _:
                    raise ValueError(dic)

        return cls(hunspell_dictionaries=tuple(hunspell_dictionaries),
                   plaintext_dictionaries=tuple(plaintext_dictionaries),
                   regexp_dictionaries=tuple(regexp_dictionaries))


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

    dictionaries: Config_Prover_Dictionaries = Config_Prover_Dictionaries()
    """
    Dictionaries for spellcheck.
    """

    skip_elements: tuple[type[Element], ...] = ()
    """
    Elements that should not be analyzed for spelling mistakes.
    """

    checks: Config_Prover_Checks = Config_Prover_Checks()
    """Additional checks enabled for this volume."""
