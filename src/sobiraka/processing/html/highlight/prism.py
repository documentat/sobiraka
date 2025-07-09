from typing import Iterable

import yattag
from panflute import Block, CodeBlock, RawBlock
from typing_extensions import override

from sobiraka.models.config import Config_Prism
from .abstract import JavaScriptHighlighterLibrary
from ..head import HeadTag

SUPPORTED_LANGUAGES = ('abap', 'abnf', 'actionscript', 'ada', 'adoc', 'agda', 'al', 'antlr4', 'apacheconf', 'apex',
                       'apl', 'applescript', 'aql', 'arduino', 'arff', 'arm-asm', 'armasm', 'art', 'arturo', 'asciidoc',
                       'asm6502', 'asmatmel', 'aspnet', 'atom', 'autohotkey', 'autoit', 'avdl', 'avisynth', 'avro-idl',
                       'avs', 'awk', 'bash', 'basic', 'batch', 'bbcode', 'bbj', 'bicep', 'birb', 'bison', 'bnf', 'bqn',
                       'brainfuck', 'brightscript', 'bro', 'bsl', 'c', 'cfc', 'cfscript', 'chaiscript', 'cil', 'cilk',
                       'cilk-c', 'cilk-cpp', 'cilkc', 'cilkcpp', 'clike', 'clojure', 'cmake', 'cobol', 'coffee',
                       'coffeescript', 'conc', 'concurnas', 'context', 'cooklang', 'coq', 'cpp', 'crystal', 'cs',
                       'csharp', 'cshtml', 'csp', 'css', 'css-extras', 'csv', 'cue', 'cypher', 'd', 'dart', 'dataweave',
                       'dax', 'dhall', 'diff', 'django', 'dns-zone', 'dns-zone-file', 'docker', 'dockerfile', 'dot',
                       'dotnet', 'ebnf', 'editorconfig', 'eiffel', 'ejs', 'elisp', 'elixir', 'elm', 'emacs',
                       'emacs-lisp', 'erb', 'erlang', 'eta', 'etlua', 'excel-formula', 'factor', 'false',
                       'firestore-security-rules', 'flow', 'fortran', 'fsharp', 'ftl', 'g4', 'gamemakerlanguage', 'gap',
                       'gawk', 'gcode', 'gdscript', 'gedcom', 'gettext', 'gherkin', 'git', 'gitignore', 'glsl', 'gml',
                       'gn', 'gni', 'go', 'go-mod', 'go-module', 'gradle', 'graphql', 'groovy', 'gv', 'haml',
                       'handlebars', 'haskell', 'haxe', 'hbs', 'hcl', 'hgignore', 'hlsl', 'hoon', 'hpkp', 'hs', 'hsts',
                       'html', 'http', 'ichigojam', 'icon', 'icu-message-format', 'idr', 'idris', 'iecst', 'ignore',
                       'inform7', 'ini', 'ino', 'io', 'j', 'java', 'javadoc', 'javadoclike', 'javascript',
                       'javastacktrace', 'jexl', 'jinja2', 'jolie', 'jq', 'js', 'js-extras', 'js-templates', 'jsdoc',
                       'json', 'json5', 'jsonp', 'jsstacktrace', 'jsx', 'julia', 'keepalived', 'keyman', 'kotlin', 'kt',
                       'kts', 'kum', 'kumir', 'kusto', 'latex', 'latte', 'ld', 'less', 'lilypond', 'linker-script',
                       'liquid', 'lisp', 'livescript', 'llvm', 'log', 'lolcode', 'lua', 'ly', 'magma', 'makefile',
                       'markdown', 'markup', 'markup-templating', 'mata', 'mathematica', 'mathml', 'matlab',
                       'maxscript', 'md', 'mel', 'mermaid', 'metafont', 'mizar', 'mongodb', 'monkey', 'moon',
                       'moonscript', 'mscript', 'mustache', 'n1ql', 'n4js', 'n4jsd', 'nand2tetris-hdl',
                       'nani', 'naniscript', 'nasm', 'nb', 'neon', 'nevod', 'nginx', 'nim', 'nix', 'npmignore', 'nsis',
                       'objc', 'objectivec', 'objectpascal', 'ocaml', 'odin', 'opencl', 'openqasm', 'oscript', 'oz',
                       'parigp', 'parser', 'pascal', 'pascaligo', 'pbfasm', 'pcaxis', 'pcode', 'peoplecode', 'perl',
                       'php', 'php-extras', 'phpdoc', 'plant-uml', 'plantuml', 'plsql', 'po', 'powerquery',
                       'powershell', 'pq', 'processing', 'prolog', 'promql', 'properties', 'protobuf', 'psl', 'pug',
                       'puppet', 'pure', 'purebasic', 'purescript', 'purs', 'px', 'py', 'python', 'q', 'qasm', 'qml',
                       'qore', 'qs', 'qsharp', 'r', 'racket', 'razor', 'rb', 'rbnf', 'reason', 'regex', 'rego', 'renpy',
                       'res', 'rescript', 'rest', 'rip', 'rkt', 'roboconf', 'robot', 'robotframework', 'rpy', 'rq',
                       'rss', 'ruby', 'rust', 'sas', 'sass', 'scala', 'scheme', 'sclang', 'scss', 'sh', 'sh-session',
                       'shell', 'shell-session', 'shellsession', 'shortcode', 'sln', 'smali', 'smalltalk', 'smarty',
                       'sml', 'smlnj', 'sol', 'solidity', 'solution-file', 'soy', 'sparql', 'splunk-spl', 'sqf', 'sql',
                       'squirrel', 'ssml', 'stan', 'stata', 'stylus', 'supercollider', 'svg', 'swift', 'systemd', 't4',
                       't4-cs', 't4-templating', 't4-vb', 'tap', 'tcl', 'tex', 'textile', 'toml', 'tremor', 'trickle',
                       'trig', 'troy', 'ts', 'tsconfig', 'tsx', 'tt2', 'turtle', 'twig', 'typescript', 'typoscript',
                       'uc', 'unrealscript', 'uorazor', 'uri', 'url', 'uscript', 'v', 'vala', 'vb', 'vba', 'vbnet',
                       'velocity', 'verilog', 'vhdl', 'vim', 'visual-basic', 'warpscript', 'wasm', 'web-idl', 'webidl',
                       'webmanifest', 'wgsl', 'wiki', 'wl', 'wolfram', 'wren', 'xeora', 'xeoracube', 'xls', 'xlsx',
                       'xml', 'xml-doc', 'xojo', 'xquery', 'yaml', 'yang', 'yml', 'zig')


class Prism(JavaScriptHighlighterLibrary[Config_Prism]):
    """
    Website: https://prismjs.com/
    """

    @staticmethod
    @override
    def get_core_scripts() -> Iterable[str]:
        yield 'components/prism-core.min.js'
        yield 'plugins/autoloader/prism-autoloader.min.js'

    @staticmethod
    @override
    def get_style_subpath(style: str) -> str:
        if style == 'default':
            return 'themes/prism.min.css'
        return f'themes/prism-{style}.min.css'

    @override
    def highlight(self, block: CodeBlock) -> tuple[Block, Iterable[HeadTag]]:
        language = block.classes[0] if len(block.classes) > 0 else 'plaintext'

        html = yattag.Doc()
        with html.tag('pre'):
            with html.tag('code', klass=f'language-{language}'):
                html.text(block.text)
        block = RawBlock(html.getvalue())

        return block, self.head
