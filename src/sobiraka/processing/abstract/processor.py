import re
from abc import ABCMeta
from asyncio import create_task
from collections import defaultdict
from contextlib import suppress
from functools import partial
from os.path import normpath
from typing import Callable, Generic, TypeVar

from panflute import Code, Element, Header, Image, Link, Para, Space, Str, Table, stringify
from typing_extensions import override

from sobiraka.models import Anchor, DirPage, FileSystem, Page, PageHref, Status, Syntax, UrlHref, Volume
from sobiraka.models.config import Config
from sobiraka.models.issues import BadImage, BadLink
from sobiraka.models.source.sourcefile import IdentifierResolutionError
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, MISSING, PathGoesOutsideStartDirectory, RelativePath, absolute_or_relative
from .dispatcher import Dispatcher
from .waiter import NoSourceCreatedForPath
from ..directive import BlockDirective, Directive, ManualTocDirective

B = TypeVar('B', bound='Builder')


class Processor(Dispatcher, Generic[B], metaclass=ABCMeta):

    def __init__(self, builder: B):
        super().__init__()
        self.builder: B = builder
        self.directives: dict[Page, list[Directive]] = defaultdict(list)
        self.unclosed_directives: dict[Page, BlockDirective | None] = {}

    async def process_role_doc(self, code: Code, page: Page):
        if m := re.fullmatch(r'(.+) < (.+) >', code.text, flags=re.X):
            label = m.group(1).strip()
            target_text = m.group(2)
        else:
            label = None
            target_text = code.text

        link = Link(Str(label))
        await self.process_internal_link(link, target_text, page)
        return (link,)

    @override
    async def process_directive(self, directive: Directive, page: Page) -> tuple[Element, ...]:
        self.directives[page].append(directive)
        return await super().process_directive(directive, page)

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        if header.level == 1:
            # Use the top level header as the page title
            RT[page].title = stringify(header)

            # Maybe skip numeration for the whole page
            if 'unnumbered' in header.classes:
                RT[page].skip_numeration = True

            # We don't need identifiers for H1
            header.identifier = ''

        else:
            # Generate anchor identifier if not provided
            identifier = header.identifier
            if not identifier:
                identifier = stringify(header)
                identifier = identifier.lower()
                identifier = re.sub(r'\W+', '-', identifier)

            # Remember the anchor
            anchor = Anchor(header, identifier, label=stringify(header), level=header.level)
            RT[page].anchors.append(anchor)

            # Maybe skip numeration for the section
            if 'unnumbered' in header.classes:
                RT[anchor].skip_numeration = True

        return header,

    @override
    async def process_image(self, image: Image, page: Page) -> tuple[Element, ...]:
        """
        Get the image path, process variables inside it, and make it relative to the resources directory.

        If the file does not exist, create an Issue and set `image.url` to None.
        """
        volume: Volume = page.volume
        config: Config = volume.config
        fs: FileSystem = volume.project.fs

        path = image.url.replace('$LANG', volume.lang or '')
        path = absolute_or_relative(path)
        if isinstance(path, AbsolutePath):
            path = path.relative_to('/')
        else:
            path = page.source.path_in_project.parent / path
            path = RelativePath(normpath(path))
            path = path.relative_to(volume.config.paths.resources)

        if fs.exists(config.paths.resources / path):
            image.url = str(path)
        else:
            page.issues.append(BadImage(image.url))
            image.url = None

        return (image,)

    @override
    async def process_link(self, link: Link, page: Page):
        if re.match(r'^\w+:', link.url):
            RT[page].links.add(UrlHref(link.url))
        elif page.syntax == Syntax.RST:
            page.issues.append(BadLink(link.url))
        else:
            await self.process_internal_link(link, link.url, page)

    @override
    async def process_para(self, para: Para, page: Page) -> tuple[Element, ...]:
        para, = await super().process_para(para, page)
        assert isinstance(para, Para)

        with suppress(AssertionError):
            assert len(para.content) >= 1
            assert isinstance(para.content[0], Str)
            assert para.content[0].text.startswith('//')

            text = ''
            for elem in para.content:
                assert isinstance(elem, (Str, Space))
                text += stringify(elem)

        return (para,)

    @override
    async def process_table(self, table: Table, page: Page) -> tuple[Element, ...]:
        table, = await super().process_table(table, page)
        assert isinstance(table, Table)

        # Remove the width specification from all columns
        for i, (align, _) in enumerate(table.colspec):
            table.colspec[i] = align, 'ColWidthDefault'

        return table,

    # region Process links

    async def process_internal_link(self, elem: Link, target_text: str, page: Page):
        # If we are inside a @manual-toc directive, prepare to report any generated links to it.
        # Note that the actual link processing will be called asynchronously in an arbitrary order,
        # and yet we will have to report the generated PageHrefs in the order of their appearance on the Page.
        # The solution is to reserve the position now, while we are inside the consecutive tree processing,
        # and create a callback that will replace the value at this position with a PageHref later.
        callback = None
        if isinstance(self.unclosed_directives.get(page), ManualTocDirective):
            manual_toc: ManualTocDirective = self.unclosed_directives[page]
            manual_toc.hrefs.append(MISSING)
            pos = len(manual_toc.hrefs) - 1
            callback = partial(manual_toc.hrefs.__setitem__, pos)

        # Schedule the actual link processing for the next stage
        self.builder.process2_tasks[page].append(create_task(
            self.process_internal_link_2(elem, target_text, page, callback)))

    async def process_internal_link_2(self, elem: Link, target_text: str, page: Page,
                                      callback: Callable[[PageHref], None] = None):
        # pylint: disable=too-many-locals
        try:
            m = re.fullmatch(r'(?: \$ ([A-z0-9\-_]+)? )? (/)? ([^#]+)? (?: [#] (.+) )?$', target_text, re.VERBOSE)
            volume_name, is_absolute, target_path_str, identifier = m.groups()

            # If the link is empty or starts with a #, it leads to the current Source
            if (volume_name, is_absolute, target_path_str) == (None, None, None):
                target = page.source

            # For any other link, find the Source by the relative or absolute path
            else:
                volume = page.volume
                if volume_name is not None:
                    volume = page.volume.project.get_volume(volume_name)
                    is_absolute = True

                target_path = RelativePath(target_path_str or '.')
                if not is_absolute:
                    if isinstance(page, DirPage):
                        target_path = (page.path_in_volume / target_path).resolve()
                    else:
                        path_in_volume = page.source.path_in_project.relative_to(volume.root_path)
                        target_path = RelativePath(normpath(path_in_volume.parent / target_path))
                target_path = volume.config.paths.root / target_path

                # Wait until the Waiter finds the Source by the path and loads its pages and anchors
                target = await self.builder.waiter.wait(target_path, Status.PROCESS1)

            # Resolve the link and update the elem accordingly
            href = target.href(identifier)
            elem.url = self.builder.make_internal_url(href, page=page)
            if not elem.content and href.default_label:
                elem.content = Str(href.default_label),

            # Add the link to the list of the page's links
            RT[page].links.add(href)
            if callback is not None:
                callback(href)

        except DisableLink:
            i = elem.parent.content.index(elem)
            elem.parent.content[i:i + 1] = elem.content

        except (KeyError, AssertionError, PathGoesOutsideStartDirectory, NoSourceCreatedForPath,
                IdentifierResolutionError):
            page.issues.append(BadLink(target_text))

        except Exception as exc:
            raise exc

    # endregion


class DisableLink(Exception):
    pass
