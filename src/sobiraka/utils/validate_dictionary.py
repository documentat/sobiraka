import re
import sys
from pathlib import Path

# TODO: Refactor validate_dictionary()
# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=unused-variable

def validate_dictionary(dic_path: Path, *, autofix: bool = False) -> 0:
    criticals: dict[tuple[Path, int], str] = {}
    warnings: dict[tuple[Path, int], str] = {}
    modifications: dict[tuple[Path, int], tuple[str, str]] = {}
    deletions: dict[tuple[Path, int], str] = {}

    aff_path = dic_path.with_suffix('.aff')

    aff = aff_path.read_bytes()
    dic = dic_path.read_bytes()

    first_line = aff.splitlines()[0]
    if m := re.fullmatch(rb'SET (\w+)', first_line):
        encoding = m.group(1)
    else:
        encoding = 'utf-8'

    files: dict[Path, list] = {}
    aff = files[aff_path] = aff.decode(encoding).splitlines()
    dic = files[dic_path] = dic.decode(encoding).splitlines()

    aff_ids: set[str] = set()

    i = -1
    while i < len(aff) - 2:
        i += 1

        if m := re.fullmatch(r'(SFX|PFX) (\w+) (Y|N) (\d+)', aff[i]):
            aff_start = i
            aff_type, aff_id, aff_yesno, aff_size = m.groups()
            aff_size = int(aff_size)

            if aff_id in aff_ids:
                criticals[aff_path, aff_start] = f'Identifier already used earlier: {aff_id}'
            else:
                aff_ids.add(aff_id)
                if len(aff_id) > 1:
                    criticals[aff_path, aff_start] = f'Identifier longer than one character: {aff_id}'

            while True:
                i += 1
                try:
                    assert aff[i] != ''
                    assert re.fullmatch(rf'SFX {aff_id} (0|\w+) (0|\w+)(/\w+)? \S+', aff[i])
                except (IndexError, AssertionError):
                    actual_size = i - aff_start - 1
                    if actual_size != aff_size:
                        fixed_line = f'{aff_type} {aff_id} {aff_yesno} {actual_size}'
                        modifications[aff_path, aff_start] = \
                            f'Wrong affix size for {aff_id} (should be {actual_size})', fixed_line
                    break
            continue

    dic_size = int(dic[0])

    for i in range(1, len(dic)):
        if dic[i] == '':
            deletions[dic_path, i] = 'Empty line in dictionaty file'
        elif m := re.fullmatch(r'([^/\s]*) (?: / (\w+) )?', dic[i], flags=re.VERBOSE):
            word, word_flags = m.groups()
            for word_flag in word_flags or ():
                if word_flag not in aff_ids:
                    criticals[dic_path, i] = f'Unknown affix: {word_flag}'
        else:
            criticals[dic_path, i] = f'Wrong dictionary line format: {dic[i]}'

    actual_dic_size = len(dic) - 1
    if dic_size != actual_dic_size:
        modifications[dic_path, 0] = f'Wrong dictionary size (should be {actual_dic_size})', str(actual_dic_size)

    for (path, i), message in sorted(criticals.items()):
        print(f'\033[31m[CRITICAL] {path.name}:{i} — {message}\033[0m', file=sys.stderr)
    for (path, i), message in sorted(warnings.items()):
        print(f'\033[33m[WARNING] {path.name}:{i} — {message}\033[0m', file=sys.stderr)

    if autofix and not criticals:
        for (path, i), (message, fixed_line) in modifications.items():
            files[path][i] = fixed_line
        for (path, i), message in reversed(sorted(deletions.items())):
            del files[path][i]
        aff_path.write_text('\n'.join(aff))
        dic_path.write_text('\n'.join(dic))
        prefix = '\033[32m[FIXED]'
    else:
        prefix = '\033[34m[FIXABLE]'

    modifications_and_deletions: dict[tuple[Path, int], str] = {}
    for (path, i), (message, fixed_line) in modifications.items():
        modifications_and_deletions[path, i] = message
    for (path, i), message in deletions.items():
        modifications_and_deletions[path, i] = message

    for (path, i), message in sorted(modifications_and_deletions.items()):
        print(f'{prefix} {path.name}:{i} — {message}\033[0m', file=sys.stderr)

    if autofix and not any((criticals, warnings)):
        return 0
    if not any((criticals, warnings, modifications, deletions)):
        return 0
    return 1
