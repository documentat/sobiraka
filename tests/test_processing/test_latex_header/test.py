from unittest import main

from abstracttests.latexprojecttestcase import LatexProjectTestCase
from abstracttests.projectdirtestcase import ProjectDirTestCase


class TestLatexHeader(LatexProjectTestCase, ProjectDirTestCase):
    pass


del LatexProjectTestCase, ProjectDirTestCase

if __name__ == '__main__':
    main()
