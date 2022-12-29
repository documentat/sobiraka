import json
import re

from sobiraka.models import Page
from sobiraka.runtime import RT


def save_debug_json(suffix: str, page: Page):
    if RT.TMP is None:
        return

    content = json.dumps(page.doc.to_json(), ensure_ascii=False, indent=2)
    content = re.sub(r'"pandoc-api-version": \[\s*(\d+),\s*(\d+),\s*(\d+)\s*]',
                     r'"pandoc-api-version": [\1, \2, \3]',
                     content)
    content = re.sub(r'{\s*"t": "Str",\s*"c": "([^\n]+)"\s*}',
                     r'{"t": "Str", "c": "\1"}',
                     content)
    content = re.sub(r'{\s*"t": "(\w+)"\s*}',
                     r'{"t": "\1"}',
                     content)
    content = re.sub(r'\[\s*"",\s*\[],\s*\[]\s*]',
                     r'["", [], []]',
                     content)

    debug_path = page.relative_path.with_suffix(f'.{suffix}.json')
    debug_path = RT.TMP / 'content' / debug_path
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(content)
