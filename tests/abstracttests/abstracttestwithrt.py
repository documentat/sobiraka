from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase

from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath


class AbstractTestWithRtTmp(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()

        temp_dir = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        RT.TMP = AbsolutePath(temp_dir)

    async def asyncTearDown(self):
        await super().asyncTearDown()

        RT.TMP = None


class AbstractTestWithRtPages(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        RT.init_context_vars()
        await super().asyncSetUp()
