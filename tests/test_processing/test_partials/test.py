from unittest import main

from abstracttests.webprojecttestcase import WebProjectTestCase


class TestPartial(WebProjectTestCase):
    pass


del WebProjectTestCase

if __name__ == '__main__':
    main()
