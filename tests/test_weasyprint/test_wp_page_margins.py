from textwrap import dedent
from unittest import main
from unittest.mock import Mock

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.processing import WeasyPrintBuilder
from sobiraka.utils import RelativePath


class TestWeasyPrint_PageMargins(WeasyPrintProjectTestCase):
    def _init_processor(self):
        builder: WeasyPrintBuilder = super()._init_processor()
        builder.theme.static_pseudofiles['printable.css'] = 'text/css', dedent('''
            html {
                font-family: "Lato", sans-serif;
            }
            
            @page {
                margin: 10rem;
                @top-left-corner     { content: "@top-left-corner";     background: deeppink;  }
                @top-left            { content: "@top-left";            background: hotpink;   }
                @top-center          { content: "@top-center";          background: lightpink; }
                @top-right           { content: "@top-right";           background: hotpink;   }
                @top-right-corner    { content: "@top-right-corner";    background: deeppink;  }
                
                @left-top            { content: "@left-top";            background: hotpink;   }
                @left-middle         { content: "@left-middle";         background: lightpink; }
                @left-bottom         { content: "@left-bottom";         background: hotpink;   }
                
                @right-top           { content: "@right-top";           background: hotpink;   }
                @right-middle        { content: "@right-middle";        background: lightpink; }
                @right-bottom        { content: "@right-bottom";        background: hotpink;   }
                
                @bottom-left-corner  { content: "@bottom-left-corner";  background: deeppink;  }
                @bottom-left         { content: "@bottom-left";         background: hotpink;   }
                @bottom-center       { content: "@bottom-center";       background: lightpink; }
                @bottom-right        { content: "@bottom-right";        background: hotpink;   }
                @bottom-right-corner { content: "@bottom-right-corner"; background: deeppink;  }
            }
        ''').strip()
        return builder

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath(): Volume({
                RelativePath(): Page('# Look at these beautiful page margins!')
            })
        })


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
