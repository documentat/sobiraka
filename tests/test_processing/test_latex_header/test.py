from unittest import main

from abstracttests.pdfbooktestcase import PdfBookTestCase


class TestLatexHeader(PdfBookTestCase):
    pass


del PdfBookTestCase

if __name__ == '__main__':
    main()