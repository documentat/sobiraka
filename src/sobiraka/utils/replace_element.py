from panflute import Element


def replace_element(old: Element, new: Element | None):
    pos = old.container.list.index(old)
    if new is not None:
        old.container.list[pos] = new
    else:
        del old.container.list[pos]
