# Список команд

## `web`

```
sobiraka web CONFIG [--output OUTPUT] [--hide-index-html]
```

Команда собирает HTML-документацию, см. [](../21-build-html/1-web.md).

## `pdf`

```
sobiraka pdf CONFIG [VOLUME] [--output OUTPUT]
```

Команда собирает PDF-документацию с помощью WeasyPrint, см. [](../22-build-pdf/1-weasyprint.md).

## `latex`

```
sobiraka [--tmpdir TMPDIR] latex CONFIG [VOLUME] [--output OUTPUT]
```

Команда собирает PDF-документацию с помощью LaTeX, см. [](../22-build-pdf/3-latex.md).

## `check_translations`

```
sobiraka check_translations CONFIG [--strict]
```

Вспомогательная команда для работы с [мультиязычными проектами](../11-overview/03-multilang.md). Команда сравнивает версии переводов и оригиналов и делит страницы на три категории:

- _Up-to-date_ — версия перевода совпадает с версией оригинала полностью;
- _Modified_ — версия перевода совпадает с версией оригинала с точностью до мажорной составляющей;
- _Outdated_ — версия перевода значительно отличается от версии оригинала.

По умолчанию команда завершается с кодом 1, если хотя бы одна страница в проекте имеет статус “Outdated”. При использовании флага `--strict` команда завершится с кодом 1, если хотя бы одна страница в проекте имеет статус “Outdated” или “Modified”.

Пример вывода:

```
en:
  This is the primary volume
  Pages: 3
ru:
  Up-to-date pages: 1
  Modified pages: 1
    src-ru/aaa.md
  Outdated pages: 1
    src-ru/bbb.md
```

## `changelog`

```
sobiraka changelog CONFIG COMMIT1 [COMMIT2]
```

Вспомогательная команда для работы с [мультиязычными проектами](../11-overview/03-multilang.md). Команда сравнивает два любых коммита в репозитории и анализирует, как изменились версии страниц между ними.

В качестве аргументов `COMMIT1` и `COMMIT2` можно указать хеши коммитов, имена веток, тегов и любые другие выражения, поддерживаемые командой [`git rev-parse`](https://git-scm.com/docs/git-rev-parse). Если второй коммит не указан, то вместо него используется указатель `HEAD`.

Команда корректно обрабатывает случаи, когда корень тома был перемещён между версиями, если при этом не изменился идентификатор тома (см. [Проекты и тома](../11-overview/01-terms.md)). Обратите внимание, что в выводе при этом используются пути к файлам из второго коммита.

Пример вывода:

```
Version upgraded:
  en/version-upgraded.md (1.0 -> 2.4)
Text upgraded:
  en/text-upgraded.md (1.0)
Both upgraded:
  en/both-upgraded.md (1.0 -> 2.4)
Version downgraded:
  en/version-downgraded.md (2.4 -> 1.0)
Both downgraded:
  en/both-downgraded.md (2.4 -> 1.0)
Version appeared:
  en/version-appeared.md (1.0)
Version disappeared:
  en/version-disappeared.md (1.0)
```