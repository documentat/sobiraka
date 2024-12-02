from textwrap import dedent
from typing import Iterable, TYPE_CHECKING

import yattag
from panflute import Block, CodeBlock, RawBlock
from typing_extensions import override

from sobiraka.models import FileSystem
from sobiraka.models.config import Config_HighlightJS
from sobiraka.utils import RelativePath
from .abstract import JavaScriptHighlighterLibrary, LanguageCannotBeHighlighted
from ..head import HeadJsFile, HeadJsUrl, HeadTag

if TYPE_CHECKING:
    from sobiraka.processing.web import WebBuilder

# Based on https://highlightjs.org/download, the 'Common' section
COMMON_LANGUAGES = {'bash', 'c', 'cpp', 'csharp', 'css', 'diff', 'go', 'graphql', 'ini', 'java', 'javascript', 'json',
                    'kotlin', 'less', 'lua', 'makefile', 'markdown', 'objectivec', 'perl', 'php-template', 'php',
                    'plaintext', 'python-repl', 'python', 'r', 'ruby', 'rust', 'scss', 'shell', 'sql', 'swift',
                    'typescript', 'vbnet', 'wasm', 'xml', 'yaml'}

# Based on https://github.com/highlightjs/highlight.js/blob/main/SUPPORTED_LANGUAGES.md
# and the list of available libraries at https://cdnjs.com/libraries/highlight.js
# Neither gives full information by itself
SUPPORTED_LANGUAGES_AND_ALIASES = {
    '1c': [],
    'abnf': [],
    'accesslog': [],
    'ada': [],
    'arduino': ['ino'],
    'armasm': ['arm'],
    'avrasm': [],
    'actionscript': ['as'],
    'angelscript': ['asc'],
    'apache': ['apacheconf'],
    'applescript': ['osascript'],
    'arcade': [],
    'asciidoc': ['adoc'],
    'aspectj': [],
    'autohotkey': [],
    'autoit': [],
    'awk': ['mawk', 'nawk', 'gawk'],
    'bash': ['sh', 'zsh'],
    'basic': [],
    'bnf': [],
    'brainfuck': ['bf'],
    'csharp': ['cs'],
    'c': ['h'],
    'cpp': ['hpp', 'cc', 'hh', 'c++', 'h++', 'cxx', 'hxx'],
    'cal': [],
    'cos': ['cls'],
    'cmake': ['cmake.in'],
    'coq': [],
    'csp': [],
    'css': [],
    'capnproto': ['capnp'],
    'clojure': ['clj'],
    'coffeescript': ['coffee', 'cson', 'iced'],
    'crmsh': ['crm', 'pcmk'],
    'crystal': ['cr'],
    'd': [],
    'dart': [],
    'delphi': ['dpr', 'dfm', 'pas', 'pascal'],
    'diff': ['patch'],
    'django': ['jinja'],
    'dns': ['zone', 'bind'],
    'dockerfile': ['docker'],
    'dos': ['bat', 'cmd'],
    'dsconfig': [],
    'dts': [],
    'dust': ['dst'],
    'ebnf': [],
    'elixir': [],
    'elm': [],
    'erlang': ['erl'],
    'excel': ['xls', 'xlsx'],
    'fsharp': ['fs', 'fsx', 'fsi', 'fsscript'],
    'fix': [],
    'fortran': ['f90', 'f95'],
    'gcode': ['nc'],
    'gams': ['gms'],
    'gauss': ['gss'],
    'gherkin': [],
    'go': ['golang'],
    'golo': ['gololang'],
    'gradle': [],
    'graphql': ['gql'],
    'groovy': [],
    'xml': ['html', 'xhtml', 'rss', 'atom', 'xjb', 'xsd', 'xsl', 'plist', 'svg'],
    'http': ['https'],
    'haml': [],
    'handlebars': ['hbs', 'html.hbs', 'html.handlebars'],
    'haskell': ['hs'],
    'haxe': ['hx'],
    'hy': ['hylang'],
    'ini': ['toml'],
    'inform7': ['i7'],
    'irpf90': [],
    'json': ['jsonc'],
    'java': ['jsp'],
    'javascript': ['js', 'jsx'],
    'julia': ['jl'],
    'julia-repl': [],
    'kotlin': ['kt'],
    'tex': [],
    'leaf': [],
    'lasso': ['ls', 'lassoscript'],
    'less': [],
    'ldif': [],
    'lisp': [],
    'livecodeserver': [],
    'livescript': ['ls'],
    'lua': ['pluto'],
    'makefile': ['mk', 'mak', 'make'],
    'markdown': ['md', 'mkdown', 'mkd'],
    'mathematica': ['mma', 'wl'],
    'matlab': [],
    'maxima': [],
    'mel': [],
    'mercury': [],
    'mips': ['mipsasm'],
    'mizar': [],
    'mojolicious': [],
    'monkey': [],
    'moonscript': ['moon'],
    'n1ql': [],
    'nsis': [],
    'nginx': ['nginxconf'],
    'nim': ['nimrod'],
    'nix': [],
    'ocaml': ['ml'],
    'objectivec': ['mm', 'objc', 'obj-c', 'obj-c++', 'objective-c++'],
    'glsl': [],
    'openscad': ['scad'],
    'ruleslanguage': [],
    'oxygene': [],
    'pf': ['pf.conf'],
    'php': [],
    'parser3': [],
    'perl': ['pl', 'pm'],
    'plaintext': ['txt', 'text'],
    'pony': [],
    'pgsql': ['postgres', 'postgresql'],
    'powershell': ['ps', 'ps1'],
    'processing': [],
    'prolog': [],
    'properties': [],
    'protobuf': ['proto'],
    'puppet': ['pp'],
    'python': ['py', 'gyp'],
    'profile': [],
    'python-repl': ['pycon'],
    'k': ['kdb'],
    'qml': [],
    'r': [],
    'reasonml': ['re'],
    'rib': [],
    'rsl': [],
    'graph': ['instances'],
    'ruby': ['rb', 'gemspec', 'podspec', 'thor', 'irb'],
    'rust': ['rs'],
    'SAS': ['sas'],
    'scss': [],
    'sql': [],
    'p21': ['step', 'stp'],
    'scala': [],
    'scheme': [],
    'scilab': ['sci'],
    'shell': ['console'],
    'smali': [],
    'smalltalk': ['st'],
    'sml': ['ml'],
    'stan': ['stanfuncs'],
    'stata': [],
    'stylus': ['styl'],
    'subunit': [],
    'swift': [],
    'tcl': ['tk'],
    'tap': [],
    'thrift': [],
    'tp': [],
    'twig': ['craftcms'],
    'typescript': ['ts', 'tsx', 'mts', 'cts'],
    'vbnet': ['vb'],
    'vbscript': ['vbs'],
    'vhdl': [],
    'vala': [],
    'verilog': ['v'],
    'vim': [],
    'axapta': ['x++'],
    'x86asm': [],
    'xl': ['tao'],
    'xquery': ['xpath', 'xq', 'xqm'],
    'yaml': ['yml'],
    'zephir': ['zep'],
}


class HighlightJs(JavaScriptHighlighterLibrary[Config_HighlightJS]):
    """
    HighlightJS aka highlight.js aka hljs.
    Website: https://highlightjs.org/
    """

    @staticmethod
    @override
    def get_core_scripts() -> Iterable[str]:
        return 'highlight.min.js',

    @staticmethod
    @override
    def get_style_subpath(style: str) -> str:
        return f'styles/{style}.min.css'

    def __init__(self, config: Config_HighlightJS, builder: 'WebBuilder'):
        super().__init__(config, builder)

        script_path = RelativePath() / '_static' / 'js' / 'init-highlight.js'
        builder.add_file_from_data(script_path, dedent('''
            document.addEventListener('DOMContentLoaded', (event) => {
                hljs.configure({languages: []});
                hljs.initHighlightingOnLoad();
            });
        ''').lstrip())
        self.head.append(HeadJsFile(script_path))

    @staticmethod
    def normalize_language_name(shortcode: str) -> str:
        for language, aliases in SUPPORTED_LANGUAGES_AND_ALIASES.items():
            if shortcode in (language, *aliases):
                return language
        raise LanguageCannotBeHighlighted(shortcode)

    @override
    def highlight(self, block: CodeBlock) -> tuple[Block, Iterable[HeadTag]]:
        language = block.classes[0] if len(block.classes) > 0 else 'plaintext'
        language = self.normalize_language_name(language)

        head = self.head.copy()
        if language not in COMMON_LANGUAGES:
            if isinstance(self.config.location, RelativePath):
                fs: FileSystem = self.builder.project.fs
                language_file = self.config.location / 'languages' / f'{language}.min.js'
                assert fs.exists(language_file)
                head.append(HeadJsFile(language_file))
            else:
                language_url = f'{self.config.location}/languages/{language}.min.js'
                head.append(HeadJsUrl(language_url))

        html = yattag.Doc()
        with html.tag('pre'):
            with html.tag('code', klass=f'language-{language}'):
                html.text(block.text)
        block = RawBlock(html.getvalue())

        return block, head
