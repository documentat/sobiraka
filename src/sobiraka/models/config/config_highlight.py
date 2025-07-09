import re
from abc import ABCMeta
from dataclasses import dataclass
from typing import Self, final

from sobiraka.utils import RelativePath


class Config_Web_Highlight(metaclass=ABCMeta):
    """Abstract type for any highlighter configuration suitable for WebBuilder."""

    @classmethod
    def load(cls, data: str | dict[str, dict]) -> Self:
        if isinstance(data, str):
            engine, config = data, {}
        else:
            assert len(data) == 1
            engine, config = next(iter(data.items()))

        match engine:
            case 'highlightjs':
                return Config_HighlightJS.load(config or {})
            case 'prism':
                return Config_Prism.load(config or {})
            case 'pygments':
                return Config_Pygments(**(config or {}))
            case _:
                raise ValueError(engine)


class Config_Pdf_Highlight(metaclass=ABCMeta):
    """Abstract type for any highlighter configuration suitable for WeasyPrintBuilder."""

    @classmethod
    def load(cls, data: str | dict[str, dict]) -> Self:
        if isinstance(data, str):
            engine, config = data, {}
        else:
            assert len(data) == 1
            engine, config = next(iter(data.items()))

        match engine:
            case 'pygments':
                return Config_Pygments(**(config or {}))
            case _:
                raise ValueError(engine)


@dataclass(kw_only=True, frozen=True)
class JavaScriptLibraryConfig(metaclass=ABCMeta):
    """
    A configuration for a JavaScript library.

    The library can be loaded:

    - from one of the popular hardcoded CDNs,
    - from an arbitrary URL,
    - from a local directory.

    When loading from a popular CDN, the exact package name may differ depending on which CDN is used.
    The subclasses are supposed to take care of these difference, so that the user
    can easily switch between CDNs via the configuration file.
    """
    location: str | RelativePath

    @staticmethod
    @final
    def get_base_url(
            *,
            version: str,
            location: str | None,
            package: str = None,
            package_cdnjs: str = None,
            package_jsdelivr: str = None,
            package_unpkg: str = None,
    ) -> str | RelativePath:
        # pylint: disable=too-many-arguments
        location = location or 'cdnjs'

        if re.match(r'^./', location):
            return RelativePath(location)

        if re.match(r'^https://', location):
            return location

        assert version is not None
        match location:
            case 'cdnjs':
                return f'https://cdnjs.cloudflare.com/ajax/libs/{package_cdnjs or package}/{version}'
            case 'jsdelivr':
                return f'https://cdn.jsdelivr.net/{package_jsdelivr or package}@{version}'
            case 'unpkg':
                return f'https://unpkg.com/{package_unpkg or package}@{version}'

        raise ValueError(location)


@dataclass(kw_only=True, frozen=True)
class JavaScriptHighlighterLibraryConfig(JavaScriptLibraryConfig, metaclass=ABCMeta):
    """
    Same as JavaScriptLibraryConfig, but with a `style` field.
    The way this field is used is implemented in the subclasses, though.
    """
    style: str | None


@dataclass(kw_only=True, frozen=True)
class Config_HighlightJS(Config_Web_Highlight, JavaScriptHighlighterLibraryConfig):
    @classmethod
    def load(cls, data: dict) -> Self:
        return Config_HighlightJS(
            location=cls.get_base_url(
                version=data.get('version', '11.10.0'),
                location=data.get('location'),
                package_cdnjs='highlight.js',
                package_jsdelivr='gh/highlightjs/cdn-release',
                package_unpkg='@highlightjs/cdn-assets',
            ),
            style=data.get('style', 'default'),
        )


@dataclass(kw_only=True, frozen=True)
class Config_Prism(Config_Web_Highlight, JavaScriptHighlighterLibraryConfig):
    @classmethod
    def load(cls, data: dict) -> Self:
        return Config_Prism(
            location=cls.get_base_url(
                version=data.get('version', '1.29.0'),
                location=data.get('location'),
                package_cdnjs='prism',
                package_jsdelivr='npm/prismjs',
                package_unpkg='prismjs',
            ),
            style=data.get('style', 'default'),
        )


@dataclass(kw_only=True, frozen=True)
class Config_Pygments(Config_Web_Highlight, Config_Pdf_Highlight):
    style: str = 'default'
    pre_class: str = None
    code_class: str = 'pygments'
