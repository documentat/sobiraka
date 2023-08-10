from typing import final

from panflute import BlockQuote, BulletList, Caption, Citation, Cite, Code, CodeBlock, Definition, DefinitionItem, \
    DefinitionList, Div, Doc, Element, Emph, Header, HorizontalRule, Image, LineBlock, LineBreak, LineItem, Link, \
    ListContainer, ListItem, Math, Note, Null, OrderedList, Para, Plain, Quoted, RawBlock, RawInline, SmallCaps, \
    SoftBreak, Space, Span, Str, Strikeout, Strong, Subscript, Superscript, Table, TableBody, TableCell, TableFoot, \
    TableHead, TableRow, Underline

from sobiraka.models import Page


class Dispatcher:
    # pylint: disable=too-many-public-methods

    @final
    async def process_element(self, elem: Element, page: Page) -> tuple[Element, ...]:
        # pylint: disable=too-many-statements
        match elem:
            case BlockQuote():
                result = await self.process_block_quote(elem, page)
            case BulletList():
                result = await self.process_bullet_list(elem, page)
            case Caption():
                result = await self.process_caption(elem, page)
            case Citation():
                result = await self.process_citation(elem, page)
            case Cite():
                result = await self.process_cite(elem, page)
            case Code() as code:
                if page.path_in_volume.suffix == '.rst' and (role := code.attributes.get('role')):
                    result = await getattr(self, f'process_role_{role}')(code, page)
                else:
                    result = await self.process_code(code, page)
            case CodeBlock():
                result = await self.process_code_block(elem, page)
            case Definition():
                result = await self.process_definition(elem, page)
            case DefinitionItem():
                result = await self.process_definition_item(elem, page)
            case DefinitionList():
                result = await self.process_definition_list(elem, page)
            case Div():
                result = await self.process_div(elem, page)
            case Doc():
                result = await self.process_container(elem, page)
            case Emph():
                result = await self.process_emph(elem, page)
            case Header():
                result = await self.process_header(elem, page)
            case HorizontalRule():
                result = await self.process_horizontal_rule(elem, page)
            case Image():
                result = await self.process_image(elem, page)
            case LineBlock():
                result = await self.process_line_block(elem, page)
            case LineBreak():
                result = await self.process_line_break(elem, page)
            case LineItem():
                result = await self.process_line_item(elem, page)
            case Link():
                result = await self.process_link(elem, page)
            case ListItem():
                result = await self.process_list_item(elem, page)
            case Math():
                result = await self.process_math(elem, page)
            case Note():
                result = await self.process_note(elem, page)
            case Null():
                result = await self.process_null(elem, page)
            case OrderedList():
                result = await self.process_ordered_list(elem, page)
            case Para():
                result = await self.process_para(elem, page)
            case Plain():
                result = await self.process_plain(elem, page)
            case Quoted():
                result = await self.process_quoted(elem, page)
            case RawBlock():
                result = await self.process_raw_block(elem, page)
            case RawInline():
                result = await self.process_raw_inline(elem, page)
            case SmallCaps():
                result = await self.process_small_caps(elem, page)
            case SoftBreak():
                result = await self.process_soft_break(elem, page)
            case Space():
                result = await self.process_space(elem, page)
            case Span():
                result = await self.process_span(elem, page)
            case Str():
                result = await self.process_str(elem, page)
            case Strikeout():
                result = await self.process_strikeout(elem, page)
            case Strong():
                result = await self.process_strong(elem, page)
            case Subscript():
                result = await self.process_subscript(elem, page)
            case Superscript():
                result = await self.process_superscript(elem, page)
            case Table():
                result = await self.process_table(elem, page)
            case TableBody():
                result = await self.process_table_body(elem, page)
            case TableCell():
                result = await self.process_table_cell(elem, page)
            case TableFoot():
                result = await self.process_table_foot(elem, page)
            case TableHead():
                result = await self.process_table_head(elem, page)
            case TableRow():
                result = await self.process_table_row(elem, page)
            case Underline():
                result = await self.process_underline(elem, page)
            case _:
                raise TypeError(type(elem))

        match result:
            case None:
                return (elem,)
            case Element() as result:
                return (result,)
            case tuple() as result:
                return result
            case _:  # pragma: no cover
                raise TypeError(type(result))

    async def process_container(self, elem: Element, page: Page) -> Element:
        """
        Process the `elem` and modify it, if necessary.
        """
        try:
            assert isinstance(elem.content, ListContainer)
        except (AttributeError, AssertionError):
            return elem

        i = -1
        while i < len(elem.content) - 1:
            i += 1
            subelem = elem.content[i]
            if subelem is None:
                continue

            result = await self.process_element(subelem, page)

            match result:
                case Element():
                    elem.content[i] = result
                case tuple():
                    elem.content[i:i + 1] = result
                    i += len(result) - 1

        return elem

    async def process_default(self, elem: Element, page: Page) -> tuple[Element, ...]:
        return (await self.process_container(elem, page),)

    async def process_block_quote(self, elem: BlockQuote, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_bullet_list(self, elem: BulletList, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_caption(self, elem: Caption, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_citation(self, elem: Citation, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_cite(self, elem: Cite, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_code(self, elem: Code, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_code_block(self, elem: CodeBlock, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_definition(self, elem: Definition, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_definition_item(self, elem: DefinitionItem, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_definition_list(self, elem: DefinitionList, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_div(self, elem: Div, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_emph(self, elem: Emph, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_header(self, elem: Header, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_horizontal_rule(self, elem: HorizontalRule, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_image(self, elem: Image, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_line_block(self, elem: LineBlock, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_line_break(self, elem: LineBreak, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_line_item(self, elem: LineItem, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_link(self, elem: Link, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_list_item(self, elem: ListItem, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_math(self, elem: Math, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_note(self, elem: Note, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_null(self, elem: Null, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_ordered_list(self, elem: OrderedList, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_para(self, elem: Para, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_plain(self, elem: Plain, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_quoted(self, elem: Quoted, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_raw_block(self, elem: RawBlock, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_raw_inline(self, elem: RawInline, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_small_caps(self, elem: SmallCaps, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_soft_break(self, elem: SoftBreak, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_space(self, elem: Space, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_span(self, elem: Span, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_str(self, elem: Str, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_strikeout(self, elem: Strikeout, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_strong(self, elem: Strong, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_subscript(self, elem: Subscript, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_superscript(self, elem: Superscript, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_table(self, elem: Table, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_table_body(self, elem: TableBody, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_table_cell(self, elem: TableCell, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_table_foot(self, elem: TableFoot, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_table_head(self, elem: TableHead, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_table_row(self, elem: TableRow, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    async def process_underline(self, elem: Underline, page: Page) -> tuple[Element, ...]:
        return await self.process_default(elem, page)

    # pylint: disable=unused-argument
    async def process_role_doc(self, elem: Code, page: Page) -> tuple[Element, ...]:
        return (Emph(Str(elem.text)),)
