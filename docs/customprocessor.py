import re
from abc import ABCMeta
from contextlib import suppress
from os import environ
from urllib.parse import unquote

from panflute import Element, Link
from typing_extensions import override

from sobiraka.files.themes.sobiraka2025.extension import Sobiraka2025_Processor, Sobiraka2025_WeasyPrintProcessor, \
    Sobiraka2025_WebProcessor
from sobiraka.models import Page, UrlHref
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath

SOBIRAKA_DOCS_SRC = AbsolutePath(__file__).parent / 'src'
SOBIRAKA_ROOT = AbsolutePath(__file__).parent.parent

PUBLIC_REPOSITORY_URL = environ.get('PUBLIC_REPOSITORY_URL') \
                        or ('CI' in environ and (environ['GITHUB_SERVER_URL'] + '/' + environ['GITHUB_REPOSITORY'])) \
                        or None


class CustomProcessor(Sobiraka2025_Processor, metaclass=ABCMeta):

    @override
    async def process_internal_link(self, link: Link, target_text: str, page: Page) -> tuple[Element, ...]:
        """
        A minor convenience for cases where we reference Sobiraka's sources.

        In the Markdown sources, we make them point to the actual local files
        so that they are clickable on GitHub or in a programmer's IDE.

        In the rendered documentation, we try to convert them into URLs that lead to GitHub.
        However, it only works in the actual GitHub's CI variables are present
        or if the GITHUB_SERVER_URL environment variable is present.

        Also, the code validates fragment links that allow navigation to a specific substring.
        If the fragment link points to a non-existent substring, a BadLink is reported.
        """
        with suppress(AssertionError, AttributeError):
            url, fragment_link = re.fullmatch(r'([^#]*?)(#:~:text=.+)?', link.url).groups()
            path: AbsolutePath = page.project.fs.resolve(page.source.path_in_project).parent / url

            assert SOBIRAKA_ROOT in path.parents
            assert SOBIRAKA_DOCS_SRC not in path.parents
            assert SOBIRAKA_DOCS_SRC != path
            assert path.exists()

            if fragment_link:
                fragment = unquote(fragment_link.split('=', maxsplit=1)[1])
                assert fragment in path.read_text()

            if not PUBLIC_REPOSITORY_URL:
                return *link.content,

            url = '/'.join((
                PUBLIC_REPOSITORY_URL,
                'tree' if path.is_dir() else 'blob',
                environ.get('GITHUB_REF_NAME', 'master'),
                str(path.relative_to(SOBIRAKA_ROOT)),
            ))
            if fragment_link:
                url += fragment_link

            RT[page].links.add(UrlHref(url))
            link.url = url
            return link,

        return await super().process_internal_link(link, target_text, page)


class CustomWebProcessor(CustomProcessor, Sobiraka2025_WebProcessor):
    pass


class CustomWeasyPrintProcessor(CustomProcessor, Sobiraka2025_WeasyPrintProcessor):
    pass
