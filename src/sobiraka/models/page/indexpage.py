from .page import Page


class IndexPage(Page):
    """
    A page that is created from index.md or a similar file in a directory.
    The only difference from a normal Page is in how the Location is created.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = self.location.parent
        if self.location.is_root:
            self.parent = None
