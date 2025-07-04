# API для обработчиков

Обработчик страниц (processor) — это один из классов Собираки, которые выполняют обработку содержимого перед финальным рендерингом файлов.

{% include 'unstable-api.md' %}

Стандартными реализациями обработчиков являются классы [`WebProcessor`](../../../src/sobiraka/processing/web/web.py), [`WeasyPrintProcessor`](../../../src/sobiraka/processing/weasyprint/weasyprint.py) и [`LatexProcessor`](../../../src/sobiraka/processing/latex/latex.py), но если конфигурация проекта или используемая тема содержит файл с собственным обработчиком, он будет загружен и использован вместо стандартного. В зависимости от проекта, вам может быть полезно унаследовать свой обработчик не от стандартной реализации, а от реализации, которая включена в используемую тему.

Экземпляр обработчика создаётся для каждого [тома](../overview/terms.md#volume), в котором этот обработчик должен использоваться.

К моменту обработки Собирака уже выполнила парсинг исходного кода с помощью [Pandoc](https://pandoc.org/) и [Panflute](http://scorreia.com/software/panflute/) и получила объект синтаксического дерева `Doc`, а также выполнила предварительный поиск и обработку [директив](../syntax/directives.md). Точкой входа в обработчик является метод `process_doc()`: ему передаётся объект `Doc`, и ожидается, что он вернёт его же после обработки. Стандартная реализация `process_doc()` рекурсивно вызывает методы [`process_*()`](#process) для вложенных элементов.

:::note
Выберите обработчик для вашего проекта одним из двух способов.

- Включите его в состав темы, заданной в [`web.theme`](configuration.md#web.theme), [`pdf.theme`](configuration.md#pdf.theme) или [`latex.theme`](configuration.md#latex.theme).
- Укажите путь к файлу Python в [`web.processor`](configuration.md#web.processor), [`pdf.processor`](configuration.md#pdf.processor) или [`latex.processor`](configuration.md#latex.processor).
:::

## `process_*()` {#process}

```python
async def process_image(self, image: Image, page: Page): ...
async def process_para(self, para: Para, page: Page): ...
async def process_table(self, table: Table, page: Page): ...
```

Большинство методов в обработчике имеют названия вида `process_*()` и предназначены для обработки одного элемента синтаксического дерева. В подавляющем большинстве случаев один метод соответствует одному классу из библиотеки [Panflute](http://scorreia.com/software/panflute/), который, в свою очередь, соответствует типу элемента в [Pandoc](https://pandoc.org/).

Полный список методов `process_*()` и логику их вызова можно найти в абстрактном классе [`Dispatcher`](../../../src/sobiraka/processing/abstract/dispatcher.py), который является предком всех обработчиков. Почти для всех элементов реализация по умолчанию рекурсивно обходит все дочерние элементы и вызывает соответствующие методы для них.

Каждый метод должен возвращать кортеж из объектов класса `Element`. Во многих ситуациях имеет смысл возвращать кортеж из одного исходного элемента, предварительно вызвав реализацию метода по умолчанию, чтобы обработать дочерние объекты. Если вместо этого вернуть пустой кортеж, элемент будет удалён из дерева. Также, возвращая нужный кортеж, можно заменить элемент на один или несколько других элементов.

:::example
**Пример.** Этот обработчик добавляет ссылку-якорь к каждому заголовку, кроме заголовка первого уровня.

```python
class MyWebProcessor(WebProcessor):
    async def process_header(self, header: Header, page: Page):
        header, = await super().process_header(header, page)
        if header.level >= 2:
            url = '#' + header.identifier
            header.content += Space(), Link(Str('#'), url=url)
        return header,
```
:::

## `process_div_*()` {#process_div}

```python
async def process_div_example(self, div: Div, page: Page): ...
```

Если элемент класса `Div` имеет один и только один класс (например, заданный через [fenced divs](https://pandoc.org/MANUAL.html#extension-fenced_divs) в Markdown), Собирака попробует обработать его методом `process_div_*()`, подставив класс вместо `*`. При отсутствии нужного метода будет вызван обычный `process_div()`.

:::example
**Пример.** Этот обработчик преобразует все блоки, оформленные с помощью конструкции `:::example`, в HTML-теги `<blockquote>` с классом `admonition-example`.

```python
class MyWebProcessor(WebProcessor):
    async def process_div_example(self, div: Div, page: Page):
        div, = await self.process_container(div, page)
        return RawBlock('<blockquote class="admonition-example">'), \
               *div.content, \
               RawBlock('</blockquote>')
```
:::

## `process_role_*()` {#process_role}

```python
async def process_role_doc(self, code: Code, page: Page): ...
```

Эта часть API актуальна только для формата [ReST](../overview/rest.md).

Методы с такими именами вызываются для обработки элементов (формально принадлежащих классу `Code`) с определёнными [ролями](https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html).

:::example
**Пример.** Этот обработчик преобразует конструкции вида `` :ui:`Настройки` `` в HTML-теги `<span>` с классом `ui`.

```python
class MyWebProcessor(WebProcessor):
    async def process_role_ui(self, code: Code, page: Page):
        code, = await super().process_container(code, page)
        return Span(*code.content, classes=['ui']),
```
:::

## `must_skip()` {#must_skip}

```python
async def must_skip(self, elem: Element, page: Page) -> bool: ...
```

Если для какого-то элемента этот метод возвращает `True`, то обработчик удаляет из дерева элемент и все его дочерние элементы.

Такого же поведения можно добиться, возвращая пустой кортеж из соответствующего метода [`process_*()`](#process), но с помощью `must_skip()` можно реализовать логику более глобально, не дублируя код между разными методами.