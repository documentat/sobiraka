from io import StringIO

from panflute import Doc, Element, dump


def panflute_to_bytes(doc: Doc) -> bytes:
    with StringIO() as stringio:
        dump(doc, stringio)
        return stringio.getvalue().encode('utf-8')


def replace_element(old: Element, new: Element | None):
    pos = old.container.list.index(old)
    if new is not None:
        old.container.list[pos] = new
    else:
        del old.container.list[pos]


def insert_after(elem: Element, new_elem: Element):
    pos = elem.container.list.index(elem)
    elem.container.insert(pos + 1, new_elem)
