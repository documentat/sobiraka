import json
from copy import copy
from dataclasses import asdict, dataclass, field
from enum import Enum

from panflute import Element


class SearchIndexerName(Enum):
    PAGEFIND = 'pagefind'


class Config_Search_LinkTarget(Enum):
    H1 = 'h1'
    H2 = 'h2'
    H3 = 'h3'
    H4 = 'h4'
    H5 = 'h5'
    H6 = 'h6'

    @property
    def level(self) -> int:
        return int(self.value[-1])


@dataclass(kw_only=True, frozen=True)
class Config_Pagefind_Translations:
    # pylint: disable=too-many-instance-attributes
    placeholder: str = None
    clear_search: str = None
    load_more: str = None
    search_label: str = None
    filters_label: str = None
    zero_results: str = None
    many_results: str = None
    one_result: str = None
    alt_search: str = None
    search_suggestion: str = None
    searching: str = None

    def to_json(self) -> str:
        """
        Returns a JSON object with all non-empty translations.
        """
        translations = asdict(self)
        for key, value in copy(translations).items():
            if value is None:
                del translations[key]
        return json.dumps(translations, ensure_ascii=False)


@dataclass(kw_only=True, frozen=True)
class Config_Web_Search:
    engine: SearchIndexerName = None
    index_path: str = None
    skip_elements: tuple[type[Element], ...] = ()
    link_target: Config_Search_LinkTarget = Config_Search_LinkTarget.H1
    translations: Config_Pagefind_Translations = field(default_factory=Config_Pagefind_Translations)
