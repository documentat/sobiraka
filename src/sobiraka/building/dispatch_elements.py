from panflute import BlockQuote, BulletList, Caption, Citation, Cite, Code, CodeBlock, Definition, DefinitionItem, DefinitionList, Div, Element, Emph, Header, HorizontalRule, Image, LineBlock, LineBreak, LineItem, Link, ListContainer, ListItem, Math, Note, Null, OrderedList, Para, Plain, Quoted, RawBlock, RawInline, SmallCaps, SoftBreak, Space, Span, Str, Strikeout, Strong, Subscript, Superscript, Table, TableBody, TableCell, TableFoot, TableHead, TableRow, Underline

from sobiraka.models import Page


class DispatchElementsTrait:

    async def process_element(self, elem: Element, page: Page) -> None | Element | tuple[Element, ...]:
        """
        Process the `elem` and modify it, if necessary.
        """
        try:
            assert isinstance(elem.content, ListContainer)
        except (AttributeError, AssertionError):
            return

        i = -1
        while i < len(elem.content) - 1:
            i += 1
            subelem = elem.content[i]

            function = {
                BlockQuote: self.process_block_quote,
                BulletList: self.process_bullet_list,
                Caption: self.process_caption,
                Citation: self.process_citation,
                Cite: self.process_cite,
                Code: self.process_code,
                CodeBlock: self.process_code_block,
                Definition: self.process_definition,
                DefinitionItem: self.process_definition_item,
                DefinitionList: self.process_definition_list,
                Div: self.process_div,
                Emph: self.process_emph,
                Header: self.process_header,
                HorizontalRule: self.process_horizontal_rule,
                Image: self.process_image,
                LineBlock: self.process_line_block,
                LineBreak: self.process_line_break,
                LineItem: self.process_line_item,
                Link: self.process_link,
                ListItem: self.process_list_item,
                Math: self.process_math,
                Note: self.process_note,
                Null: self.process_null,
                OrderedList: self.process_ordered_list,
                Para: self.process_para,
                Plain: self.process_plain,
                Quoted: self.process_quoted,
                RawBlock: self.process_raw_block,
                RawInline: self.process_raw_inline,
                SmallCaps: self.process_small_caps,
                SoftBreak: self.process_soft_break,
                Space: self.process_space,
                Span: self.process_span,
                Str: self.process_str,
                Strikeout: self.process_strikeout,
                Strong: self.process_strong,
                Subscript: self.process_subscript,
                Superscript: self.process_superscript,
                Table: self.process_table,
                TableBody: self.process_table_body,
                TableCell: self.process_table_cell,
                TableFoot: self.process_table_foot,
                TableHead: self.process_table_head,
                TableRow: self.process_table_row,
                Underline: self.process_underline,
            }[type(subelem)]

            result  = await function(subelem, page)

            match result:
                case None:
                    pass
                case Element():
                    elem.content[i] = result
                case tuple():
                    elem.content[i:i + 1] = result
                    i += len(result) - 1
                case _:  # pragma: no cover
                    raise TypeError(type(result))

        return elem

    async def process_block_quote(self, elem: BlockQuote, page: Page):          return await self.process_element(elem, page)
    async def process_bullet_list(self, elem: BulletList, page: Page):          return await self.process_element(elem, page)
    async def process_caption(self, elem: Caption, page: Page):                 return await self.process_element(elem, page)
    async def process_citation(self, elem: Citation, page: Page):               return await self.process_element(elem, page)
    async def process_cite(self, elem: Cite, page: Page):                       return await self.process_element(elem, page)
    async def process_code(self, elem: Code, page: Page):                       return await self.process_element(elem, page)
    async def process_code_block(self, elem: CodeBlock, page: Page):            return await self.process_element(elem, page)
    async def process_definition(self, elem: Definition, page: Page):           return await self.process_element(elem, page)
    async def process_definition_item(self, elem: DefinitionItem, page: Page):  return await self.process_element(elem, page)
    async def process_definition_list(self, elem: DefinitionList, page: Page):  return await self.process_element(elem, page)
    async def process_div(self, elem: Div, page: Page):                         return await self.process_element(elem, page)
    async def process_emph(self, elem: Emph, page: Page):                       return await self.process_element(elem, page)
    async def process_header(self, elem: Header, page: Page):                   return await self.process_element(elem, page)
    async def process_horizontal_rule(self, elem: HorizontalRule, page: Page):  return await self.process_element(elem, page)
    async def process_image(self, elem: Image, page: Page):                     return await self.process_element(elem, page)
    async def process_line_block(self, elem: LineBlock, page: Page):            return await self.process_element(elem, page)
    async def process_line_break(self, elem: LineBreak, page: Page):            return await self.process_element(elem, page)
    async def process_line_item(self, elem: LineItem, page: Page):              return await self.process_element(elem, page)
    async def process_link(self, elem: Link, page: Page):                       return await self.process_element(elem, page)
    async def process_list_item(self, elem: ListItem, page: Page):              return await self.process_element(elem, page)
    async def process_math(self, elem: Math, page: Page):                       return await self.process_element(elem, page)
    async def process_note(self, elem: Note, page: Page):                       return await self.process_element(elem, page)
    async def process_null(self, elem: Null, page: Page):                       return await self.process_element(elem, page)
    async def process_ordered_list(self, elem: OrderedList, page: Page):        return await self.process_element(elem, page)
    async def process_para(self, elem: Para, page: Page):                       return await self.process_element(elem, page)
    async def process_plain(self, elem: Plain, page: Page):                     return await self.process_element(elem, page)
    async def process_quoted(self, elem: Quoted, page: Page):                   return await self.process_element(elem, page)
    async def process_raw_block(self, elem: RawBlock, page: Page):              return await self.process_element(elem, page)
    async def process_raw_inline(self, elem: RawInline, page: Page):            return await self.process_element(elem, page)
    async def process_small_caps(self, elem: SmallCaps, page: Page):            return await self.process_element(elem, page)
    async def process_soft_break(self, elem: SoftBreak, page: Page):            return await self.process_element(elem, page)
    async def process_space(self, elem: Space, page: Page):                     return await self.process_element(elem, page)
    async def process_span(self, elem: Span, page: Page):                       return await self.process_element(elem, page)
    async def process_str(self, elem: Str, page: Page):                         return await self.process_element(elem, page)
    async def process_strikeout(self, elem: Strikeout, page: Page):             return await self.process_element(elem, page)
    async def process_strong(self, elem: Strong, page: Page):                   return await self.process_element(elem, page)
    async def process_subscript(self, elem: Subscript, page: Page):             return await self.process_element(elem, page)
    async def process_superscript(self, elem: Superscript, page: Page):         return await self.process_element(elem, page)
    async def process_table(self, elem: Table, page: Page):                     return await self.process_element(elem, page)
    async def process_table_body(self, elem: TableBody, page: Page):            return await self.process_element(elem, page)
    async def process_table_cell(self, elem: TableCell, page: Page):            return await self.process_element(elem, page)
    async def process_table_foot(self, elem: TableFoot, page: Page):            return await self.process_element(elem, page)
    async def process_table_head(self, elem: TableHead, page: Page):            return await self.process_element(elem, page)
    async def process_table_row(self, elem: TableRow, page: Page):              return await self.process_element(elem, page)
    async def process_underline(self, elem: Underline, page: Page):             return await self.process_element(elem, page)