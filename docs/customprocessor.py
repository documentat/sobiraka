from abc import ABCMeta
from os import environ

from panflute import Element, Link
from typing_extensions import override

from sobiraka.files.themes.sobiraka2025.extension import Sobiraka2025_Processor, Sobiraka2025_WeasyPrintProcessor, \
    Sobiraka2025_WebProcessor
from sobiraka.models import Page, UrlHref
from sobiraka.models.issues import BadLink
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath

SOBIRAKA_DOCS_SRC = AbsolutePath(__file__).parent / 'src'
SOBIRAKA_ROOT = AbsolutePath(__file__).parent.parent

SOBIRAKA_REPOSITORY = environ.get('SOBIRAKA_REPOSITORY') \
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
        """
        path: AbsolutePath = page.project.fs.resolve(page.source.path_in_project).parent / link.url
        if SOBIRAKA_ROOT in path.parents \
                and SOBIRAKA_DOCS_SRC not in path.parents \
                and SOBIRAKA_DOCS_SRC != path:
            if not path.exists():
                page.issues.append(BadLink(target_text))
                return link,

            if not SOBIRAKA_REPOSITORY:
                return *link.content,

            link.url = '/'.join((
                SOBIRAKA_REPOSITORY,
                'tree' if path.is_dir() else 'blob',
                environ.get('GITHUB_REF_NAME', 'master'),
                str(path.relative_to(SOBIRAKA_ROOT)),
            ))
            RT[page].links.add(UrlHref(link.url))
            return link,

        return await super().process_internal_link(link, target_text, page)


class CustomWebProcessor(CustomProcessor, Sobiraka2025_WebProcessor):
    pass


class CustomWeasyPrintProcessor(CustomProcessor, Sobiraka2025_WeasyPrintProcessor):
    pass
