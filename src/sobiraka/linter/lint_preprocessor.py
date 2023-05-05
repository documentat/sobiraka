from asyncio import gather
from collections import defaultdict
from typing import Awaitable, Callable

from panflute import BlockQuote, BulletList, Caption, Citation, Cite, Code, CodeBlock, Definition, DefinitionItem, DefinitionList, Div, Element, Emph, Header, HorizontalRule, Image, LineBlock, LineBreak, LineItem, Link, ListItem, Math, Note, Null, OrderedList, Para, Plain, Quoted, RawBlock, RawInline, SmallCaps, SoftBreak, Space, Span, Str, Strikeout, Strong, Subscript, Superscript, Table, TableBody, TableCell, TableFoot, TableHead, TableRow, Underline

from sobiraka.models import Page, Project
from sobiraka.processing.abstract import Processor
from .exceptions_regexp import exceptions_regexp
from .textmodel import Fragment, Pos, TextModel


class LintPreprocessor(Processor):

    def __init__(self, project: Project):
        super().__init__(project)

        regexp = exceptions_regexp(self.project.volumes[0])
        self._tm: dict[Page, TextModel] = defaultdict(lambda: TextModel(exceptions_regexp=regexp))

    async def tm(self, page: Page) -> TextModel:
        await self.process2(page)
        return self._tm[page]

    async def preprocess(self):
        tasks: list[Awaitable] = []
        for page in self.project.pages:
            tasks.append(self.process2(page))
        await gather(*tasks)

    def _atomic(self, page: Page, elem: Element, text: str):
        assert '\n' not in text

        tm = self._tm[page]

        start = tm.end_pos
        tm.lines[-1] += text
        end = tm.end_pos

        fragment = Fragment(tm, start, end, elem)
        tm.fragments.append(fragment)

    async def _container(self, page: Page, elem: Element, *,
                         allow_new_line: bool = False,
                         process: Callable[[], Awaitable[None]] = None):
        tm = self._tm[page]

        start = tm.end_pos
        f = len(tm.fragments)

        if process is not None:
            await process()
        else:
            await self.process_container(elem, page)

        end = tm.end_pos
        if not allow_new_line:
            assert start.line == end.line, 'Processing an inline container produced extra newlines.'

        fragment = Fragment(tm, start, end, elem)
        tm.fragments.insert(f, fragment)

    def _ensure_new_line(self, page: Page):
        tm = self._tm[page]
        if tm.lines[-1] != '':
            tm.lines.append('')

    ################################################################################
    # Inline non-containers

    async def process_code(self, elem: Code, page: Page):
        self._atomic(page, elem, elem.text)

    async def process_space(self, elem: Space, page: Page):
        self._atomic(page, elem, ' ')

    async def process_str(self, elem: Str, page: Page):
        self._atomic(page, elem, elem.text)

    async def process_line_break(self, elem: LineBreak, page: Page):
        tm = self._tm[page]
        pos = Pos(len(tm.lines) - 1, len(tm.lines[-1]))
        fragment = Fragment(tm, pos, pos, elem)
        tm.fragments.append(fragment)
        tm.lines.append('')

    ################################################################################
    # Inline containers

    async def process_emph(self, elem: Emph, page: Page):
        await self._container(page, elem)

    async def process_strong(self, elem: Strong, page: Page):
        await self._container(page, elem)

    async def process_image(self, elem: Image, page: Page):
        await self._container(page, elem)

    async def process_link(self, elem: Link, page: Page):
        await self._container(page, elem)

    async def process_plain(self, elem: Plain, page: Page):
        await self._container(page, elem)

    async def process_small_caps(self, elem: SmallCaps, page: Page):
        await self._container(page, elem)

    async def process_span(self, elem: Span, page: Page):
        await self._container(page, elem)

    async def process_strikeout(self, elem: Strikeout, page: Page):
        await self._container(page, elem)

    async def process_underline(self, elem: Underline, page: Page):
        await self._container(page, elem)

    ################################################################################
    # Block containers

    async def process_block_quote(self, elem: BlockQuote, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_definition(self, elem: Definition, page: Page):
        await self._container(page, elem, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_definition_item(self, elem: DefinitionItem, page: Page):
        async def process():
            for subelem in elem.term:
                await self.process_element(subelem, page)
            self._ensure_new_line(page)
            for subelem in elem.definitions:
                await self.process_element(subelem, page)
                self._ensure_new_line(page)
        await self._container(page, elem, allow_new_line=True, process=process)

    async def process_definition_list(self, elem: DefinitionList, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_div(self, elem: Div, page: Page):
        await self._container(page, elem, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_header(self, elem: Header, page: Page):
        await self._container(page, elem, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_para(self, elem: Para, page: Page):
        await self._container(page, elem, allow_new_line=True)
        self._ensure_new_line(page)

    ################################################################################
    # Lists

    async def process_bullet_list(self, elem: BulletList, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_ordered_list(self, elem: OrderedList, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_list_item(self, elem: ListItem, page: Page):
        await self._container(page, elem, allow_new_line=True)
        self._ensure_new_line(page)

    ################################################################################
    # Tables

    async def process_table(self, elem: Table, page: Page):
        async def process():
            await self.process_table_head(elem.head, page)
            await self.process_table_body(elem.content[0], page)
            await self.process_table_foot(elem.foot, page)
            await self.process_caption(elem.caption, page)
        await self._container(page, elem, allow_new_line=True, process=process)

    async def process_table_body(self, elem: TableBody, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_table_cell(self, elem: TableCell, page: Page):
        await self._container(page, elem, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_table_foot(self, elem: TableFoot, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_table_head(self, elem: TableHead, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_table_row(self, elem: TableRow, page: Page):
        await self._container(page, elem, allow_new_line=True)

    async def process_caption(self, elem: Caption, page: Page):
        await self._container(page, elem, allow_new_line=True)
        self._ensure_new_line(page)

    ################################################################################
    # Line blocks

    async def process_line_block(self, elem: LineBlock, page: Page):
        tm = self._tm[page]
        async def process():
            for i, line_item in enumerate(elem.content):
                if i != 0:
                    tm.lines[-1] += ' '
                await self._container(page, line_item)
        await self._container(page, elem, allow_new_line=True, process=process)
        self._ensure_new_line(page)

    async def process_line_item(self, elem: LineItem, page: Page):
        await self._container(page, elem)

    ################################################################################
    # Ignored elements

    async def process_code_block(self, elem: CodeBlock, page: Page): pass
    async def process_horizontal_rule(self, elem: HorizontalRule, page: Page): pass
    async def process_math(self, elem: Math, page: Page): pass
    async def process_raw_block(self, elem: RawBlock, page: Page): pass
    async def process_raw_inline(self, elem: RawInline, page: Page): pass
    async def process_subscript(self, elem: Subscript, page: Page): pass
    async def process_superscript(self, elem: Superscript, page: Page): pass

    ################################################################################
    # Rarely used elements, not implemented

    async def process_citation(self, elem: Citation, page: Page):     return await self.process_default(elem, page)
    async def process_cite(self, elem: Cite, page: Page):             return await self.process_default(elem, page)
    async def process_note(self, elem: Note, page: Page):             return await self.process_default(elem, page)
    async def process_null(self, elem: Null, page: Page):             await self.process_default(elem, page)
    async def process_quoted(self, elem: Quoted, page: Page):         return await self.process_default(elem, page)
    async def process_soft_break(self, elem: SoftBreak, page: Page):  await self.process_default(elem, page)

    ################################################################################

    async def process_default(self, elem: Element, page: Page):
        raise NotImplementedError(elem.__class__.__name__)