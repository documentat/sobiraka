import sys
from enum import Enum

from sobiraka.models import Page
from sobiraka.models.project import Project
from sobiraka.models.version import TranslationStatus


def check_translations(project: Project, *, strict: bool) -> int:
    ok = True

    for volume in project.volumes:
        print(f'{volume.autoprefix}:', file=sys.stderr)

        if volume is project.primary_volume:
            _print(_Color.GREEN, '  This is the primary volume')
            _print(_Color.GREEN, f'  Pages: {len(project.primary_volume.pages)}')

        else:
            pages: dict[TranslationStatus, list[Page]] = {status: [] for status in TranslationStatus}

            for page in volume.pages:
                pages[page.translation_status].append(page)

            _print(_Color.GREEN, f'  Up-to-date pages: {len(pages[TranslationStatus.UPTODATE])}')
            _print(_Color.YELLOW, f'  Modified pages: {len(pages[TranslationStatus.MODIFIED])}')
            for page in pages[TranslationStatus.MODIFIED]:
                _print(_Color.YELLOW, f'    {page.path_in_project}')
            _print(_Color.RED, f'  Outdated pages: {len(pages[TranslationStatus.OUTDATED])}')
            for page in pages[TranslationStatus.OUTDATED]:
                _print(_Color.RED, f'    {page.path_in_project}')

            if (strict and len(pages[TranslationStatus.MODIFIED]) > 0) \
                    or len(pages[TranslationStatus.OUTDATED]) > 0:
                ok = False

    return 0 if ok else 1


class _Color(Enum):
    GREEN = 32
    YELLOW = 33
    RED = 31


def _print(color: _Color, text: str):
    print(f'\033[{color.value}m{text}\033[0m', file=sys.stderr)
