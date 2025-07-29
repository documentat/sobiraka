import unittest

from panflute import Doc, Header, Image, Para, SoftBreak, Space, Str

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from helpers.fakefilesystem import PseudoFiles
from sobiraka.models.config import Config, Config_Content, Config_Paths
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class TestEmojiReplacements(SinglePageProjectTest):
    SOURCE = '''
        # 🔵 Emoji Examples
        🟢 Replaceable
        🟠 Irreplaceable
    '''

    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(
                root=RelativePath('src'),
                resources=RelativePath('img'),
            ),
            content=Config_Content(
                emoji_replacements={
                    '🔵': '/blue.png',
                    '🟢': '/green.png',
                },
            ),
        )

    def additional_files(self) -> PseudoFiles:
        return {
            'img/blue.png': b'',
            'img/green.png': b'',
        }

    def test_doc(self):
        expected = Doc(
            Header(Image(url='blue.png'), Space(), Str('Emoji'), Space(), Str('Examples')),
            Para(
                Image(url='green.png'), Space(), Str('Replaceable'),
                SoftBreak(),
                Str('🟠'), Space(), Str('Irreplaceable'),
            ),
        ).content
        actual = RT[self.page].doc.content
        self.assertEqual(expected, actual)


del SinglePageProjectTest

if __name__ == '__main__':
    unittest.main()
