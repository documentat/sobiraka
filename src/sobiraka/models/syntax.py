from enum import Enum


class Syntax(Enum):
    HTML = 'html'
    MD = 'md'
    RST = 'rst'

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    def as_pandoc_format(self) -> str:
        match self:
            case self.MD:
                return 'markdown-smart-raw_html-raw_tex-implicit_figures+mark'
            case self.RST:
                return 'rst-auto_identifiers'
