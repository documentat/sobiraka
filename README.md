# Собирака

**Собирака** — сборщик документации, разработанный в [Documentat](https://documentat.io/). Собирака основана на популярных проектах с открытым исходным кодом, таких как Pandoc и LaTeX, но добавляет к ним свои правила и проверки.

Сборщик ориентирован на подход «docs as code» и поддерживает [Markdown](https://sobiraka.documentat.io/writing/markdown.html) и [reStructuredText](https://sobiraka.documentat.io/writing/rest.html), в том числе с возможностью совмещать их в одном проекте. Вне зависимости от языка разметки, Собирака проверяет корректность всех [внутренних ссылок](https://sobiraka.documentat.io/writing/links.html) в рамках проекта. Также в исходных файлах поддерживаются условия, инклюды и другие [конструкции Jinja](https://sobiraka.documentat.io/writing/jinja.html).

Готовая документация собирается в форматах [HTML](https://sobiraka.documentat.io/build-html/) и [PDF](https://sobiraka.documentat.io/build-pdf/). Для формата HTML поддерживается [поиск по документации](https://sobiraka.documentat.io/overview/search.html). В рамках одного проекта возможно собирать [несколько документов](https://sobiraka.documentat.io/overview/terms.html), в том числе [на разных языках](https://sobiraka.documentat.io/overview/multilang.html).

Собирака предоставляет богатые возможности по кастомизации процесса сборки: от [шаблонов для HTML](https://sobiraka.documentat.io/web/customization.html#template) до [произвольного кода на Python](https://sobiraka.documentat.io/reference/processor-api.html).