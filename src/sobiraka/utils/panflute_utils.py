from io import StringIO

import panflute


def panflute_to_bytes(doc: panflute.Doc) -> bytes:
    with StringIO() as stringio:
        panflute.dump(doc, stringio)
        return stringio.getvalue().encode('utf-8')