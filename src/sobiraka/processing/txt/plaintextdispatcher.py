from collections import defaultdict
from typing import Awaitable, Callable

from panflute import BlockQuote, BulletList, Caption, Citation, Cite, Code, CodeBlock, Definition, DefinitionItem, \
    DefinitionList, Div, Doc, Element, Emph, Header, HorizontalRule, Image, LineBlock, LineBreak, LineItem, Link, \
    ListItem, Math, Note, Null, OrderedList, Para, Plain, Quoted, RawBlock, RawInline, SmallCaps, SoftBreak, Space, \
    Span, Str, Strikeout, Strong, Subscript, Superscript, Table, TableBody, TableCell, TableFoot, TableHead, TableRow, \
    Underline

from sobiraka.models import Anchor, Page
from sobiraka.processing.abstract import Dispatcher
from sobiraka.runtime import RT

from .textmodel import Fragment, Pos, TextModel


class PlainTextDispatcher(Dispatcher):
    """
    Base class for features that need to work with text, such as linters or indexers.

    It works as a :class:`Dispatcher`, analyzing each element in the Panflute tree.
    Unlike some other dispatchers/processors, it is non-destructive: it never modifies or removes elements.

    Once :meth:`process_doc()` is done, you can retrieve the information about the plain text
    from :data:`tm`, which is a :class:`TextModel` object.
    """
    # pylint: disable=too-many-public-methods

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tm: dict[Page, TextModel] = defaultdict(self._new_text_model)

        self._current_section_anchor: dict[Page, Anchor | None] = defaultdict(lambda: None)
        self._current_section_start: dict[Page, Pos] = defaultdict(lambda: Pos(0, 0))

    async def process_doc(self, doc: Doc, page: Page):
        await self.process_container(doc, page)

        # If we just started a new line at the end, remove it, we don't need it
        tm = self.tm[page]
        if tm.lines[-1] == '':
            tm.lines = tm.lines[:-1]

        # Close the section related to the latest found header.
        # If there were no headers, this will close the section related to `None`,
        # i.e. the main section that began at Pos(0, 0), as defined in the init.
        anchor = self._current_section_anchor[page]
        start = self._current_section_start[page]
        end = tm.end_pos
        tm.sections[anchor] = Fragment(tm, start, max(start, end))

        # Indicate that the TextModel data is now final
        tm.freeze()

    def _new_text_model(self) -> TextModel:
        return TextModel()

    def _atomic(self, page: Page, elem: Element, text: str):
        """
        For a single inline element (such as a `Str` or a `Space`),
        append a given text representation to the current line and create a corresponding :class:`Fragment`.
        """
        assert '\n' not in text

        tm = self.tm[page]

        start = tm.end_pos
        tm.lines[-1] += text
        end = tm.end_pos

        tm.fragments.append(Fragment(tm, start, end, elem))

    async def _container(self, page: Page, elem: Element, *,
                         allow_new_line: bool = False,
                         process: Callable[[], Awaitable[None]] = None):
        tm = self.tm[page]

        start = tm.end_pos
        pos = len(tm.fragments)

        if process is not None:
            await process()
        else:
            await self.process_container(elem, page)

        end = tm.end_pos
        if not allow_new_line:
            assert start.line == end.line, 'Processing an inline container produced extra newlines.'

        tm.fragments.insert(pos, Fragment(tm, start, end, elem))

    def _ensure_new_line(self, page: Page):
        tm = self.tm[page]
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
        tm = self.tm[page]
        fragment = Fragment(tm, tm.end_pos, tm.end_pos, line_break)
        tm.fragments.append(fragment)
        tm.lines.append('')

    async def process_soft_break(self, soft_break: SoftBreak, page: Page):
        tm = self.tm[page]
        tm.fragments.append(Fragment(tm, tm.end_pos, tm.end_pos, soft_break))
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
        tm = self.tm[page]

        # Close previous section
        tm.sections[self._current_section_anchor[page]] = Fragment(tm, self._current_section_start[page], tm.end_pos)

        # Process the content inside the header
        await self._container(page, header, allow_new_line=True)
        self._ensure_new_line(page)

        # Start a new section
        if header.level > 1:
            self._current_section_anchor[page] = RT[page].anchors.by_header(header)
            self._current_section_start[page] = tm.end_pos

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
        tm = self.tm[page]

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
