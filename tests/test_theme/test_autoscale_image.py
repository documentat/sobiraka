import unittest
from abc import ABCMeta
from io import BytesIO

import PIL.Image
from panflute import Image

from abstracttests.projecttestcase import T
from abstracttests.singlepageprojecttest import SinglePageProjectTest
from helpers.fakefilesystem import PseudoFiles
from sobiraka.models import Status
from sobiraka.models.config import Config, Config_Paths
from sobiraka.processing.web import WebBuilder
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class TestAutoscaleImage(SinglePageProjectTest, metaclass=ABCMeta):
    REQUIRE = Status.PROCESS1

    EXPECTED_SIZE: tuple[str, str]

    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(
                root=RelativePath('src'),
                resources=RelativePath('resources'),
            ),
        )

    def _init_builder(self) -> T:
        return WebBuilder(self.project, None)

    def additional_files(self) -> PseudoFiles:
        with BytesIO() as image:
            PIL.Image.new('RGB', (300, 200)).save(image, 'PNG')
            image_bytes = image.getvalue()

        return {
            'resources/image.png': image_bytes,
        }

    def test_image_size(self):
        image = RT[self.page].doc.content[0].content[0].content[0].content[0]
        self.assertIsInstance(image, Image)
        with self.subTest('width'):
            self.assertEqual(self.EXPECTED_SIZE[0], image.attributes.get('width'))
        with self.subTest('height'):
            self.assertEqual(self.EXPECTED_SIZE[1], image.attributes.get('height'))


class TestAutoscaleImage_Default(TestAutoscaleImage):
    SOURCE = '![](/image.png)'
    EXPECTED_SIZE = '300px', '200px'


class TestAutoscaleImage_Explicit(TestAutoscaleImage):
    SOURCE = '![](/image.png){width=400px height=700px}'
    EXPECTED_SIZE = '400px', '700px'


class TestAutoscaleImage_Width_100percent(TestAutoscaleImage):
    SOURCE = '![](/image.png){width=100%}'
    EXPECTED_SIZE = '100%', '66.66666666666667%'


class TestAutoscaleImage_Width_50percent(TestAutoscaleImage):
    SOURCE = '![](/image.png){width=50%}'
    EXPECTED_SIZE = '50%', '33.333333333333336%'


class TestAutoscaleImage_Width_150px(TestAutoscaleImage):
    SOURCE = '![](/image.png){width=150px}'
    EXPECTED_SIZE = '150px', '100.0px'


class TestAutoscaleImage_Height_100px(TestAutoscaleImage):
    SOURCE = '![](/image.png){height=100px}'
    EXPECTED_SIZE = '150.0px', '100px'


del SinglePageProjectTest, TestAutoscaleImage

if __name__ == '__main__':
    unittest.main()
