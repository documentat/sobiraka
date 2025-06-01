from argparse import ArgumentParser
from dataclasses import dataclass
from math import inf

from more_itertools import map_reduce, unique_everseen
from panflute import Block
from typing_extensions import override

from sobiraka.models import PageHref
from sobiraka.models.config import CombinedToc
from sobiraka.models.issues import Issue
from sobiraka.processing.toc import local_toc, toc
from .directive import BlockDirective


class ManualTocDirective(BlockDirective):
    DIRECTIVE_NAME = 'manual-toc'

    local: bool
    combined: bool

    depth: int
    ordered: bool
    unique: bool

    @classmethod
    @override
    def set_up_arguments(cls, parser: ArgumentParser):
        local_or_combined = parser.add_mutually_exclusive_group()
        local_or_combined.add_argument('--local', action='store_true')
        local_or_combined.add_argument('--combined', action='store_true')

        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--ordered', action='store_true')
        parser.add_argument('--unique', action='store_true')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hrefs: list[PageHref] = []

    @override
    def postprocess(self) -> Block | None:
        if self.local:
            expected_toc = local_toc(self.page,
                                     builder=self.builder,
                                     toc_depth=self.depth,
                                     current_page=self.page)
        else:
            expected_toc = toc(self.page,
                               builder=self.builder,
                               toc_depth=self.depth,
                               combined_toc=CombinedToc.from_bool(self.combined),
                               current_page=self.page)

        expected_hrefs: list[PageHref] = list(x.href for x in expected_toc.walk())
        actual_hrefs: list[PageHref] = list(x for x in self.hrefs if x in expected_hrefs)

        if self.unique:
            for href, href_entries in map_reduce(actual_hrefs, lambda x: x).items():
                if len(href_entries) > 1:
                    self.page.issues.append(DuplicateTocItem(href.url_relative_to(self.page), len(href_entries)))

        if self.ordered:
            expected_order = list(x for x in expected_hrefs if x in actual_hrefs)
            actual_order = list(unique_everseen(actual_hrefs))
            if actual_order != expected_order:
                self.page.issues.append(WrongTocOrder())

        for href in expected_hrefs:
            if href not in actual_hrefs:
                self.page.issues.append(MissingTocLink(href.url_relative_to(self.page)))


@dataclass(order=True, frozen=True)
class DuplicateTocItem(Issue):
    url: str
    count: int

    def __str__(self):
        return f'Link appears {self.count} times in manual TOC: {self.url}'


@dataclass(order=True, frozen=True)
class WrongTocOrder(Issue):
    def __str__(self):
        return 'Wrong order in manual TOC.'


@dataclass(order=True, frozen=True)
class MissingTocLink(Issue):
    url: str

    def __str__(self):
        return f'Missing link in manual TOC: {self.url}'
