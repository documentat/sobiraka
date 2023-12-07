from pathlib import Path

from sobiraka.models import IndexPage, Page, TocTreeItem


def dataset_paths(ext: str) -> dict[Path, Page]:
    return {
        Path() / f'0-index.{ext}': IndexPage('# root'),
        Path() / 'part1' / f'0-index.{ext}': IndexPage('# part1'),
        Path() / 'part1' / 'chapter1' / f'0-index.{ext}': IndexPage('# chapter1'),
        Path() / 'part1' / 'chapter1' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part1' / 'chapter1' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter1' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part1' / 'chapter1' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part1' / 'chapter1' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter1' / 'section2' / f'article2.{ext}': Page('# article2'),
        Path() / 'part1' / 'chapter2' / f'0-index.{ext}': IndexPage('# chapter2'),
        Path() / 'part1' / 'chapter2' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part1' / 'chapter2' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter2' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part1' / 'chapter2' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part1' / 'chapter2' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter2' / 'section2' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / f'0-index.{ext}': IndexPage('# part2'),
        Path() / 'part2' / 'chapter1' / f'0-index.{ext}': IndexPage('# chapter1'),
        Path() / 'part2' / 'chapter1' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part2' / 'chapter1' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter1' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / 'chapter1' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part2' / 'chapter1' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter1' / 'section2' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / 'chapter2' / f'0-index.{ext}': IndexPage('# chapter2'),
        Path() / 'part2' / 'chapter2' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part2' / 'chapter2' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter2' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / 'chapter2' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part2' / 'chapter2' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter2' / 'section2' / f'article2.{ext}': Page('# article2'),
    }


def dataset_expected_items(toc_expansion: int | float) -> list[TocTreeItem]:
    return [
        TocTreeItem('part1', 'part1/index.html', **_children_if(toc_expansion > 1, [
            TocTreeItem('chapter1', 'part1/chapter1/index.html', **_children_if(toc_expansion > 2, [
                TocTreeItem('section1', 'part1/chapter1/section1/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part1/chapter1/section1/article1.html'),
                    TocTreeItem('article2', 'part1/chapter1/section1/article2.html'),
                ])),
                TocTreeItem('section2', 'part1/chapter1/section2/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part1/chapter1/section2/article1.html'),
                    TocTreeItem('article2', 'part1/chapter1/section2/article2.html'),
                ])),
            ])),
            TocTreeItem('chapter2', 'part1/chapter2/index.html', **_children_if(toc_expansion > 2, [
                TocTreeItem('section1', 'part1/chapter2/section1/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part1/chapter2/section1/article1.html'),
                    TocTreeItem('article2', 'part1/chapter2/section1/article2.html'),
                ])),
                TocTreeItem('section2', 'part1/chapter2/section2/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part1/chapter2/section2/article1.html'),
                    TocTreeItem('article2', 'part1/chapter2/section2/article2.html'),
                ])),
            ])),
        ])),
        TocTreeItem('part2', 'part2/index.html', **_children_if(toc_expansion > 1, [
            TocTreeItem('chapter1', 'part2/chapter1/index.html', **_children_if(toc_expansion > 2, [
                TocTreeItem('section1', 'part2/chapter1/section1/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part2/chapter1/section1/article1.html'),
                    TocTreeItem('article2', 'part2/chapter1/section1/article2.html'),
                ])),
                TocTreeItem('section2', 'part2/chapter1/section2/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part2/chapter1/section2/article1.html'),
                    TocTreeItem('article2', 'part2/chapter1/section2/article2.html'),
                ])),
            ])),
            TocTreeItem('chapter2', 'part2/chapter2/index.html', **_children_if(toc_expansion > 2, [
                TocTreeItem('section1', 'part2/chapter2/section1/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part2/chapter2/section1/article1.html'),
                    TocTreeItem('article2', 'part2/chapter2/section1/article2.html'),
                ])),
                TocTreeItem('section2', 'part2/chapter2/section2/index.html', **_children_if(toc_expansion > 3, [
                    TocTreeItem('article1', 'part2/chapter2/section2/article1.html'),
                    TocTreeItem('article2', 'part2/chapter2/section2/article2.html'),
                ])),
            ])),
        ])),
    ]


def _children_if(value: bool, children: list[TocTreeItem]):
    return dict(children=children) if value else dict(is_collapsed=True)