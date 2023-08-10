# check_translations

::: warning
Документация по скрипту пока не написана, но можно почитать про [мультиязычность](../1-concepts/2-multilang.md).
:::

По умолчанию скрипт завершается с кодом 1, если хотя бы одна страница в проекте имеет статус “Outdated”. При использовании флага `--strict` скрипт завершится с кодом 1, если хотя бы одна страница в проекте имеет статус “Outdated” или “Modified”.

## Пример вывода

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
