from panflute import Element


def replace_element(old: Element, new: Element):
    pos = old.container.list.index(old)
    old.container.list[pos] = new
