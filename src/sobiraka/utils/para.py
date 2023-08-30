from panflute import Block, Para


class WrapperPara(Para):
    tag = 'Para'

    def __init__(self, original_elem: Block, *args):
        super().__init__(*args)
        self.original_elem: Block = original_elem
