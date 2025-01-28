from importlib.resources import files
from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers import FakeFileSystem
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.models.config import Config, Config_PDF
from sobiraka.utils import AbsolutePath, RelativePath

CSS = b'''
html {
    font-family: "Lato", sans-serif;
}

div.toc {
    display: none;
}

@page {
    margin: 10rem !important;
    
    @top-left-corner     { content: "@top-left-corner"     !important; background: deeppink;  }
    @top-left            { content: "@top-left"            !important; background: hotpink;   }
    @top-center          { content: "@top-center"          !important; background: lightpink; }
    @top-right           { content: "@top-right"           !important; background: hotpink;   }
    @top-right-corner    { content: "@top-right-corner"    !important; background: deeppink;  }
    
    @left-top            { content: "@left-top"            !important; background: hotpink;   }
    @left-middle         { content: "@left-middle"         !important; background: lightpink; }
    @left-bottom         { content: "@left-bottom"         !important; background: hotpink;   }
    
    @right-top           { content: "@right-top"           !important; background: hotpink;   }
    @right-middle        { content: "@right-middle"        !important; background: lightpink; }
    @right-bottom        { content: "@right-bottom"        !important; background: hotpink;   }
    
    @bottom-left-corner  { content: "@bottom-left-corner"  !important; background: deeppink;  }
    @bottom-left         { content: "@bottom-left"         !important; background: hotpink;   }
    @bottom-center       { content: "@bottom-center"       !important; background: lightpink; }
    @bottom-right        { content: "@bottom-right"        !important; background: hotpink;   }
    @bottom-right-corner { content: "@bottom-right-corner" !important; background: deeppink;  }
}
'''


class TestWeasyPrint_PageMargins(SinglePageProjectTest, WeasyPrintProjectTestCase):
    SOURCE = '''
        # Look at these beautiful page margins!
    '''

    def _init_filesystem(self) -> FileSystem:
        return FakeFileSystem({
            RelativePath('theme/style.css'): CSS,
        })

    def _init_config(self) -> Config:
        return Config(
            pdf=Config_PDF(
                theme=AbsolutePath(files('sobiraka')) / 'files' / 'themes' / 'raw',
                custom_styles=(
                    RelativePath('theme/style.css'),
                )))


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
