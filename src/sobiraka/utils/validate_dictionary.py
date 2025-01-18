import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from colorama import Fore, Style


@dataclass
class HunspellFileIssue:
    lineno: int
    message: str


@dataclass
class Critical(HunspellFileIssue):
    pass


@dataclass
class Deletable(HunspellFileIssue):
    pass


@dataclass
class Fixable(HunspellFileIssue):
    replacement: str


@dataclass
class Fixed(HunspellFileIssue):
    pass


@dataclass
class HunspellFile:
    path: Path
    encoding: str

    lines: list[str] = field(default_factory=list)

    issues: list[HunspellFileIssue] = field(default_factory=list)

    def __post_init__(self):
        self.lines = self.path.read_text(self.encoding).splitlines()

    def __str__(self):
        return self.path.name

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, i: int) -> str:
        return self.lines[i]

    def __setitem__(self, i: int, line: str):
        self.lines[i] = line

    def can_autofix(self) -> bool:
        for issue in self.issues:
            if isinstance(issue, Critical):
                return False
        return True

    def autofix(self):
        fixables = list(x for x in self.issues if isinstance(x, Fixable))
        deletables = list(x for x in self.issues if isinstance(x, Deletable))
        assert len(fixables) + len(deletables) == len(self.issues)

        for issue in fixables:
            self.lines[issue.lineno] = issue.replacement
        for issue in reversed(sorted(deletables, key=lambda x: x.lineno)):
            del self.lines[issue.lineno]

        self.path.write_text('\n'.join(self.lines), self.encoding)

        self.issues = list(Fixed(x.lineno, x.message) for x in self.issues)

    def messages(self) -> Iterable[str]:
        colors = {
            Critical: Fore.RED,
            Deletable: Fore.YELLOW,
            Fixable: Fore.YELLOW,
            Fixed: Fore.GREEN,
        }
        labels = {
            Critical: '[CRITICAL]',
            Deletable: '[FIXABLE]',
            Fixable: '[FIXABLE]',
            Fixed: '[FIXED]',
        }
        for issue in sorted(self.issues, key=lambda x: x.lineno):
            color = colors[type(issue)]
            label = labels[type(issue)]
            yield f'{color}{label:<11} {self}:{issue.lineno} — {issue.message}'


@dataclass
class Aff(HunspellFile):
    ids: set[str] = field(default_factory=set)


@dataclass
class Dic(HunspellFile):
    pass


class DictionaryValidator:
    def __init__(self, aff_path: Path, dic_path: Path):
        # Read the DIC's first line to determine the encoding
        with dic_path.open() as f:
            first_line = f.readline()
            if m := re.fullmatch(r'SET (\w+)', first_line):
                encoding = m.group()
            else:
                encoding = 'utf-8'

        # Read both files with the selected encoding
        self.aff = Aff(aff_path, encoding)
        self.dic = Dic(dic_path, encoding)

    def run(self, autofix: bool) -> int:
        self.validate()

        exit_code = 0
        if self.aff.issues or self.dic.issues:
            if autofix and self.can_autofix():
                self.autofix()
                exit_code = 0
            else:
                exit_code = 1

        for message in self.messages():
            print(message, file=sys.stderr)
        print(Style.RESET_ALL, file=sys.stderr)

        return exit_code

    def validate(self):
        self._validate_aff()
        self._validate_dic()

    def _validate_aff(self):
        aff = self.aff

        i = -1
        while i < len(aff) - 2:
            i += 1

            if m := re.fullmatch(r'(SFX|PFX) (\w+) (Y|N) (\d+)', aff[i]):
                aff_start = i
                aff_type, aff_id, aff_yesno, aff_size = m.groups()
                aff_size = int(aff_size)

                if aff_id in aff.ids:
                    aff.issues.append(Critical(aff_start, f'Identifier already used earlier: {aff_id}'))
                else:
                    aff.ids.add(aff_id)
                    if len(aff_id) > 1:
                        aff.issues.append(Critical(aff_start, f'Identifier longer than one character: {aff_id}'))

                while True:
                    i += 1
                    try:
                        assert aff[i] != ''
                        assert re.fullmatch(rf'SFX {aff_id} (0|\w+) (0|\w+)(/\w+)? \S+', aff[i])
                    except (IndexError, AssertionError):
                        actual_size = i - aff_start - 1
                        if actual_size != aff_size:
                            aff.issues.append(Fixable(aff_start,
                                                      f'Wrong affix size for {aff_id} (should be {actual_size})',
                                                      f'{aff_type} {aff_id} {aff_yesno} {actual_size}'))
                        break
                continue

    def _validate_dic(self):
        aff = self.aff
        dic = self.dic

        dic_size = int(dic[0])

        for i in range(1, len(dic)):
            if dic[i] == '':
                dic.issues.append(Deletable(i, 'Empty line in dictionary file'))
            elif m := re.fullmatch(r'([^/\s]*) (?: / (\w+) )?', dic[i], flags=re.VERBOSE):
                word_flags = m.group(2)
                for word_flag in word_flags or ():
                    if word_flag not in aff.ids:
                        dic.issues.append(Critical(i, f'Unknown affix: {word_flag}'))
            else:
                dic.issues.append(Critical(i, f'Wrong dictionary line format: {dic[i]}'))

        actual_dic_size = len(dic) - 1
        if dic_size != actual_dic_size:
            dic.issues.append(Fixable(0, f'Wrong dictionary size (should be {actual_dic_size})', str(actual_dic_size)))

    def can_autofix(self) -> bool:
        return self.aff.can_autofix() and self.dic.can_autofix()

    def autofix(self):
        self.aff.autofix()
        self.dic.autofix()

    def messages(self) -> Sequence[str]:
        return *self.aff.messages(), *self.dic.messages()
