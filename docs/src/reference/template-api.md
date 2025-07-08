# API для шаблонов

Переменные и функции, доступные [шаблону](../build-html/web-customization.md#template) при сборке документации в HTML.

{% include 'unstable-api.md' %}

## API для всех форматов {#all}

- [`builder`](../../../src/sobiraka/processing/abstract/builder.py) — объект-сборщик.

- [`project`](../../../src/sobiraka/models/project.py) — текущий проект.

- [`volume`](../../../src/sobiraka/models/volume.py) — текущий [том](../overview/terms.md).

- [`config`](../../../src/sobiraka/models/config/config.py) — объект для доступа к настройкам текущего тома.

- [`head`](../../../src/sobiraka/processing/html/head.py) — дополнительный код, который необходимо добавить внутрь тега `<head>`.

- [`toc()`](../../../src/sobiraka/processing/toc.py#:~:text=def%20toc) — функция, генерирующая оглавление по текущему тому.

## API для сборки HTML {#html}

- `number` — номер страницы, если в томе включена [автонумерация](../writing/numeration.md).

- `title` — заголовок страницы.

- `body` — содержимое страницы без заголовка, преобразованное в HTML.

- [`page`](../../../src/sobiraka/models/page/page.py) — объект для доступа к текущей странице.

- `ROOT` — относительный путь к корню документации. Пример: `..`.

- `ROOT_PAGE` — относительный путь к главной странице документации. Примеры: `..`, `../index.html`.

- `RESOURCES` — относительный путь к директории с изображениями и другими ресурсами. Пример: `../images`.

- `STATIC` — относительный путь к директории, в которую будут скопированы ресурсы из поддиректории `_static` используемой темы. Пример: `../static`.

- `theme_data` — словарь с произвольными данными из настройки [`web.theme_data`](configuration.md#web.theme_data).

- `now` — текущие дата и время, полученные с помощью [`datetime.now()`](https://docs.python.org/3/library/datetime.html#datetime.datetime.now).

- `Language` — класс для получения названия языка. См. библиотеку [`iso639`](https://github.com/jacksonllee/iso639).

- [`local_toc()`](../../../src/sobiraka/processing/toc.py#:~:text=def%20local_toc) — функция, генерирующая оглавление по текущей странице.

## API для сборки PDF {#pdf}

- `content` — список кортежей, каждый из которых содержит четыре элемента:

   - объект для доступа к текущей странице;
   - номер страницы, если в томе включена [автонумерация](../writing/numeration.md);
   - заголовок страницы;
   - содержимое страницы без заголовка, преобразованное в HTML.