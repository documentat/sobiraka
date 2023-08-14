import sys

from clint import textui
from clint.textui import colored

from sobiraka.models import Page
from sobiraka.models.project import Project
from sobiraka.models.version import TranslationStatus


def check_translations(project: Project, *, strict: bool) -> int:
    ok = True

    for volume in project.volumes:
        print(f'{volume.autoprefix}:', file=sys.stderr)
        with textui.indent(2):

            if volume.lang == project.primary_language:
                print(colored.green('  This is the primary volume'), file=sys.stderr)
                print(colored.green(f'  Pages: {len(volume.pages)}'), file=sys.stderr)

            else:
                pages: dict[TranslationStatus, list[Page]] = {status: [] for status in TranslationStatus}

                for page in volume.pages:
                    pages[page.translation_status].append(page)

                print(colored.green(f'  Up-to-date pages: {len(pages[TranslationStatus.UPTODATE])}'), file=sys.stderr)
                print(colored.yellow(f'  Modified pages: {len(pages[TranslationStatus.MODIFIED])}'), file=sys.stderr)
                for page in pages[TranslationStatus.MODIFIED]:
                    print(colored.yellow(f'    {page.path_in_project}'), file=sys.stderr)
                print(colored.red(f'  Outdated pages: {len(pages[TranslationStatus.OUTDATED])}'), file=sys.stderr)
                for page in pages[TranslationStatus.OUTDATED]:
                    print(colored.red(f'    {page.path_in_project}'), file=sys.stderr)

                if (strict and len(pages[TranslationStatus.MODIFIED]) > 0) \
                        or len(pages[TranslationStatus.OUTDATED]) > 0:
                    ok = False

    return 0 if ok else 1
