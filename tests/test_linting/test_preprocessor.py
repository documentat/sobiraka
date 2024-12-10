from unittest import main

from panflute import Space, Str

from abstracttests.abstractlintingtest import AbstractLintingTest
from helpers import assertNoDiff


class TestLintPreprocessor(AbstractLintingTest):
    SOURCE = r'''
        # Page
        
        Text can be **bold**, _italic_, [underline]{.underline}, [small caps]{.smallcaps}, or even `code`. Also, there can be [some **links**](https://example.com/).
        
        ----
        
        ![Image](image.png)
        
        Here's a list:
        
        - Item 1
        - Item **2**
        - `Item 3`
        
        Here's another list:
        
        -   Item 4
        
            Description
        
        -   Item 5
        
            Description
        
        Term 1
          : Definition 1
        
        Term 2
          : Definition 21
          : Definition 22
        
        Table: Expressions and values
        
        | Expression | Value |
        |------------|-------|
        | `a`        | 1     |
        | `b`        | 2     |
        | `a` + `b`  | 3     |
        
        This paragraph contains \
        A line break.
        
        > This is a block quote.
        
        ::: Warning :::
        
        This is a warning div.
        
        :::
        
        | A block
        | containing
        | multiple lines.
    '''

    EXPECTED_LINES = (
        'Page',
        'Text can be bold, italic, underline, small caps, or even code. Also, there can be some links.',
        'Image',
        "Here's a list:",
        'Item 1',
        'Item 2',
        'Item 3',
        "Here's another list:",
        'Item 4',
        'Description',
        'Item 5',
        'Description',
        'Term 1',
        'Definition 1',
        'Term 2',
        'Definition 21',
        'Definition 22',
        'Expression',
        'Value',
        'a',
        '1',
        'b',
        '2',
        'a + b',
        '3',
        'Expressions and values',
        'This paragraph contains',
        'A line break.',
        'This is a block quote.',
        'This is a warning div.',
        'A block containing multiple lines.',
    )

    EXPECTED_PHRASES = (
        'Page',
        'Text can be bold, italic, underline, small caps, or even code.',
        'Also, there can be some links.',
        'Image',
        "Here's a list:",
        'Item 1',
        'Item 2',
        'Item 3',
        "Here's another list:",
        'Item 4',
        'Description',
        'Item 5',
        'Description',
        'Term 1',
        'Definition 1',
        'Term 2',
        'Definition 21',
        'Definition 22',
        'Expression',
        'Value',
        'a',
        '1',
        'b',
        '2',
        'a + b',
        '3',
        'Expressions and values',
        'This paragraph contains',
        'A line break.',
        'This is a block quote.',
        'This is a warning div.',
        'A block containing multiple lines.',
    )

    EXPECTED_FRAGMENTS = r'''
        [0:0-0:4][Header] Page
        
        [1:0-1:93][Para] Text can be bold, italic, underline, small caps, or even code. Also, there can be some links.
          [1:12-1:16][Strong] bold
          [1:18-1:24][Emph] italic
          [1:26-1:35][Underline] underline
          [1:37-1:47][SmallCaps] small caps
          [1:57-1:61][Code] code
          [1:82-1:92][Link] some links
            [1:87-1:92][Strong] links
        
        [2:0-2:5][Para] Image
          [2:0-2:5][Image] Image
        
        [3:0-3:14][Para] Here's a list:
        
        [4:0-7:0][BulletList] Item 1 \n Item 2 \n Item 3
          [4:0-4:6][ListItem] Item 1
            [4:0-4:6][Plain] Item 1
          [5:0-5:6][ListItem] Item 2
            [5:0-5:6][Plain] Item 2
              [5:5-5:6][Strong] 2
          [6:0-6:6][ListItem] Item 3
            [6:0-6:6][Plain] Item 3
              [6:0-6:6][Code] Item 3
        
        [7:0-7:20][Para] Here's another list:
        
        [8:0-12:0][BulletList] Item 4 \n Description \n Item 5 \n Description
          [8:0-10:0][ListItem] Item 4 \n Description
            [8:0-8:6][Para] Item 4
            [9:0-9:11][Para] Description
          [10:0-12:0][ListItem] Item 5 \n Description
            [10:0-10:6][Para] Item 5
            [11:0-11:11][Para] Description
        
        [12:0-17:0][DefinitionList] Term 1 \n Definition 1 \n Term 2 \n Definition 21 \n Definition 22
          [12:0-14:0][DefinitionItem] Term 1 \n Definition 1
            [13:0-13:12][Definition] Definition 1
              [13:0-13:12][Plain] Definition 1
          [14:0-17:0][DefinitionItem] Term 2 \n Definition 21 \n Definition 22
            [15:0-15:13][Definition] Definition 21
              [15:0-15:13][Plain] Definition 21
            [16:0-16:13][Definition] Definition 22
              [16:0-16:13][Plain] Definition 22
        
        [17:0-26:0][Table] Expression \n Value \n a \n 1 \n b \n 2 \n a + b \n 3 \n Expressions and values
          [17:0-19:0][TableHead] Expression \n Value
            [17:0-19:0][TableRow] Expression \n Value
              [17:0-17:10][TableCell] Expression
                [17:0-17:10][Plain] Expression
              [18:0-18:5][TableCell] Value
                [18:0-18:5][Plain] Value
          [19:0-25:0][TableBody] a \n 1 \n b \n 2 \n a + b \n 3
            [19:0-21:0][TableRow] a \n 1
              [19:0-19:1][TableCell] a
                [19:0-19:1][Plain] a
                  [19:0-19:1][Code] a
              [20:0-20:1][TableCell] 1
                [20:0-20:1][Plain] 1
            [21:0-23:0][TableRow] b \n 2
              [21:0-21:1][TableCell] b
                [21:0-21:1][Plain] b
                 [21:0-21:1][Code] b
              [22:0-22:1][TableCell] 2
                [22:0-22:1][Plain] 2
            [23:0-25:0][TableRow] a + b \n 3
              [23:0-23:5][TableCell] a + b
                [23:0-23:5][Plain] a + b
                  [23:0-23:1][Code] a
                  [23:4-23:5][Code] b
              [24:0-24:1][TableCell] 3
                [24:0-24:1][Plain] 3
          [25:0-25:0][TableFoot]
          [25:0-25:22][Caption] Expressions and values
            [25:0-25:22][Plain] Expressions and values
        
        [26:0-27:13][Para] This paragraph contains \n A line break.
          [26:23-26:23][LineBreak]
        
        [28:0-29:0][BlockQuote] This is a block quote.
          [28:0-28:22][Para] This is a block quote.
        
        [29:0-30:0][Div] This is a warning div.
          [29:0-29:22][Para] This is a warning div.
        
        [30:0-30:34][LineBlock] A block containing multiple lines.
          [30:0-30:7][LineItem] A block
          [30:8-30:18][LineItem] containing
          [30:19-30:34][LineItem] multiple lines.
    '''

    async def test_lines(self):
        tm = self.tm(self.page)
        actual = tm.lines
        while actual[-1] == '':
            actual.pop()

        assertNoDiff(self.EXPECTED_LINES, actual)

    async def test_fragments(self):
        expected = list(filter(None, (f.strip() for f in self.EXPECTED_FRAGMENTS.splitlines())))

        actual: list[str] = []
        tm = self.tm(self.page)
        self.assertSequenceEqual(sorted(tm.fragments, key=lambda f: f.start), tm.fragments)

        for f in tm.fragments:
            if not isinstance(f.element, (Str, Space)):
                text = f.text.strip().replace('\n', r' \n ')
                actual.append(f'[{f.start}-{f.end}][{f.element.tag}] {text}'.rstrip())

        assertNoDiff(expected, actual)


del AbstractLintingTest

if __name__ == '__main__':
    main()
