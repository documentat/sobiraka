from io import StringIO

import panflute
from panflute import Element


def panflute_to_bytes(doc: panflute.Doc) -> bytes:
    with StringIO() as stringio:
        panflute.dump(doc, stringio)
        return stringio.getvalue().encode('utf-8')


def replace_element(old: Element, new: Element | None):
    pos = old.container.list.index(old)
    if new is not None:
        old.container.list[pos] = new
    else:
        del old.container.list[pos]
