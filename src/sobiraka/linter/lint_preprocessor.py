from collections import defaultdict
from typing import Awaitable, Callable

from panflute import BlockQuote, BulletList, Caption, Citation, Cite, Code, CodeBlock, Definition, DefinitionItem, \
    DefinitionList, Div, Element, Emph, Header, HorizontalRule, Image, LineBlock, LineBreak, LineItem, Link, \
    ListItem, Math, Note, Null, OrderedList, Para, Plain, Quoted, RawBlock, RawInline, SmallCaps, SoftBreak, Space, \
    Span, Str, Strikeout, Strong, Subscript, Superscript, Table, TableBody, TableCell, TableFoot, TableHead, TableRow, \
    Underline

from sobiraka.models import Page, Volume
from sobiraka.processing.abstract import Processor
from .exceptions_regexp import exceptions_regexp
from .textmodel import Fragment, Pos, TextModel


class LintPreprocessor(Processor):
    # pylint: disable=too-many-public-methods

    def __init__(self, volume: Volume):
        super().__init__()
        self.volume: Volume = volume

        regexp = exceptions_regexp(self.volume)
        self._tm: dict[Page, TextModel] = defaultdict(lambda: TextModel(exceptions_regexp=regexp))

    async def tm(self, page: Page) -> TextModel:
        await self.process2(page)
        return self._tm[page]

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
        pos = len(tm.fragments)

        if process is not None:
            await process()
        else:
            await self.process_container(elem, page)

        end = tm.end_pos
        if not allow_new_line:
            assert start.line == end.line, 'Processing an inline container produced extra newlines.'

        fragment = Fragment(tm, start, end, elem)
        tm.fragments.insert(pos, fragment)

    def _ensure_new_line(self, page: Page):
        tm = self._tm[page]
        if tm.lines[-1] != '':
            tm.lines.append('')

    ################################################################################
    # Inline non-containers

    async def process_code(self, code: Code, page: Page):
        self._atomic(page, code, code.text)

    async def process_space(self, space: Space, page: Page):
        self._atomic(page, space, ' ')

    async def process_str(self, elem: Str, page: Page):
        self._atomic(page, elem, elem.text)

    async def process_line_break(self, line_break: LineBreak, page: Page):
        tm = self._tm[page]
        pos = Pos(len(tm.lines) - 1, len(tm.lines[-1]))
        fragment = Fragment(tm, pos, pos, line_break)
        tm.fragments.append(fragment)
        tm.lines.append('')

    async def process_soft_break(self, soft_break: SoftBreak, page: Page):
        tm = self._tm[page]
        pos = Pos(len(tm.lines) - 1, len(tm.lines[-1]))
        fragment = Fragment(tm, pos, pos, soft_break)
        tm.fragments.append(fragment)
        tm.lines.append('')

    ################################################################################
    # Inline containers

    async def process_emph(self, emph: Emph, page: Page):
        await self._container(page, emph)

    async def process_strong(self, strong: Strong, page: Page):
        await self._container(page, strong)

    async def process_image(self, image: Image, page: Page):
        await self._container(page, image)

    async def process_link(self, link: Link, page: Page):
        await super().process_link(link, page)
        await self._container(page, link)

    async def process_plain(self, plain: Plain, page: Page):
        await self._container(page, plain)

    async def process_small_caps(self, small_caps: SmallCaps, page: Page):
        await self._container(page, small_caps)

    async def process_span(self, span: Span, page: Page):
        await self._container(page, span)

    async def process_strikeout(self, strikeout: Strikeout, page: Page):
        await self._container(page, strikeout)

    async def process_underline(self, underline: Underline, page: Page):
        await self._container(page, underline)

    ################################################################################
    # Block containers

    async def process_block_quote(self, blockquote: BlockQuote, page: Page):
        await self._container(page, blockquote, allow_new_line=True)

    async def process_definition(self, definition: Definition, page: Page):
        await self._container(page, definition, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_definition_item(self, definition_item: DefinitionItem, page: Page):
        async def process():
            for subelem in definition_item.term:
                await self.process_element(subelem, page)
            self._ensure_new_line(page)
            for subelem in definition_item.definitions:
                await self.process_element(subelem, page)
                self._ensure_new_line(page)

        await self._container(page, definition_item, allow_new_line=True, process=process)

    async def process_definition_list(self, definition_list: DefinitionList, page: Page):
        await self._container(page, definition_list, allow_new_line=True)

    async def process_div(self, div: Div, page: Page):
        await self._container(page, div, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_header(self, header: Header, page: Page):
        await self._container(page, header, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_para(self, para: Para, page: Page):
        await self._container(page, para, allow_new_line=True)
        self._ensure_new_line(page)

    ################################################################################
    # Lists

    async def process_bullet_list(self, bullet_list: BulletList, page: Page):
        await self._container(page, bullet_list, allow_new_line=True)

    async def process_ordered_list(self, ordered_list: OrderedList, page: Page):
        await self._container(page, ordered_list, allow_new_line=True)

    async def process_list_item(self, item: ListItem, page: Page):
        await self._container(page, item, allow_new_line=True)
        self._ensure_new_line(page)

    ################################################################################
    # Tables

    async def process_table(self, table: Table, page: Page):
        async def process():
            await self.process_table_head(table.head, page)
            await self.process_table_body(table.content[0], page)
            await self.process_table_foot(table.foot, page)
            await self.process_caption(table.caption, page)

        await self._container(page, table, allow_new_line=True, process=process)

    async def process_table_body(self, body: TableBody, page: Page):
        await self._container(page, body, allow_new_line=True)

    async def process_table_cell(self, cell: TableCell, page: Page):
        await self._container(page, cell, allow_new_line=True)
        self._ensure_new_line(page)

    async def process_table_foot(self, foot: TableFoot, page: Page):
        await self._container(page, foot, allow_new_line=True)

    async def process_table_head(self, head: TableHead, page: Page):
        await self._container(page, head, allow_new_line=True)

    async def process_table_row(self, row: TableRow, page: Page):
        await self._container(page, row, allow_new_line=True)

    async def process_caption(self, caption: Caption, page: Page):
        await self._container(page, caption, allow_new_line=True)
        self._ensure_new_line(page)

    ################################################################################
    # Line blocks

    async def process_line_block(self, line_block: LineBlock, page: Page):
        tm = self._tm[page]

        async def process():
            for i, line_item in enumerate(line_block.content):
                if i != 0:
                    tm.lines[-1] += ' '
                await self._container(page, line_item)

        await self._container(page, line_block, allow_new_line=True, process=process)
        self._ensure_new_line(page)

    async def process_line_item(self, line_item: LineItem, page: Page):
        await self._container(page, line_item)

    ################################################################################
    # Ignored elements

    async def process_code_block(self, code: CodeBlock, page: Page):
        pass

    async def process_horizontal_rule(self, rule: HorizontalRule, page: Page):
        pass

    async def process_math(self, math: Math, page: Page):
        pass

    async def process_raw_block(self, raw: RawBlock, page: Page):
        pass

    async def process_raw_inline(self, raw: RawInline, page: Page):
        pass

    async def process_subscript(self, subscript: Subscript, page: Page):
        pass

    async def process_superscript(self, superscript: Superscript, page: Page):
        pass

    ################################################################################
    # Rarely used elements, not implemented

    async def process_citation(self, citation: Citation, page: Page):
        return await self.process_default(citation, page)

    async def process_cite(self, cite: Cite, page: Page):
        return await self.process_default(cite, page)

    async def process_note(self, note: Note, page: Page):
        return await self.process_default(note, page)

    async def process_null(self, elem: Null, page: Page):
        return await self.process_default(elem, page)

    async def process_quoted(self, quoted: Quoted, page: Page):
        return await self.process_default(quoted, page)

    ################################################################################

    async def process_default(self, elem: Element, page: Page):
        raise NotImplementedError(elem.__class__.__name__)
