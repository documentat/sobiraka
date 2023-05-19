from enum import Enum


class Syntax(Enum):
    HTML = 'html'
    MD = 'md'
    RST = 'rst'

    def as_pandoc_format(self) -> str:
        match self:
            case self.MD:
                return 'markdown-smart'
            case self.RST:
                return 'rst-auto_identifiers'
