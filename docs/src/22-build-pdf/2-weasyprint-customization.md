# Кастомизация WeasyPrint

[WeasyPrint](https://weasyprint.org/) использует собственный движок отрисовки HTML. Движок поддерживает большинство возможностей языка стилей CSS, но не поддерживает скрипты JavaScript. Полный список особенностей движка приведён в разделе [Supported Features](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html#supported-features) документации WeasyPrint.

Способы кастомизации, специфичные для генерации PDF, преимущественно связаны с поддержкой следующих стандартов:

- [CSS Paged Media](https://drafts.csswg.org/css-page-3/) (правило `@rule`, колонтитулы),
- [CSS Generated Content](https://www.w3.org/TR/css-content-3/) (свойства `content` и `string-set`),
- [CSS Lists and Counters](https://drafts.csswg.org/css-lists/) (счётчики).

## Шаблон для рендеринга страниц {#template}

{% with %}
{% set template_filename = 'print.html' %}
{% set template_is_the_only_file = False %}
{% set template_supports_search = False %}
{% include 'html-template.md' %}
{% endwith %}

## Статические файлы {#static-files}

Все файлы, необходимые для корректного отображения темы (стили, изображения, шрифты), должны находиться в поддиректории `_static` рядом с шаблоном. Шаблон должен ссылаться на эти файлы через относительные пути, например:

```html
<link rel='stylesheet' href='_static/theme.css'/>
```

## Плагин для обработки страниц {#plugin}

В файле `theme.py` может быть определён _плагин_ — код на Python для дополнительной обработки содержимого перед рендерингом.

Класс плагина должен наследоваться от класса `sobiraka.processing.plugin.WeasyPrintTheme`. Плагин имеет почти неограниченные возможности в рамках обработки отдельной страницы, см. [](../99-reference/4-plugin-api.md).

## Нумерация заголовков {#autonumeration}

Нумерация для каждого заголовка (или информация о том, что этот заголовок не нумеруется) доступна через объект `RT` в момент применения темы. Один из способов перенести эту информацию в документ — в коде `theme.py` привести её к строке и записать в атрибут `data-number` заголовка (вы можете использовать другое название атрибута). Пример ниже реализует это для заголовков первого уровня:

```python
class MyTheme(WeasyPrintTheme):
    async def process_header(self, header: Header, page: Page):
        if header.level == 1:
            header.attributes['data-number'] = str(RT[page].number)
```

Стиль CSS может сослаться на содержимое этого атрибута через функцию [`attr()`](https://drafts.csswg.org/css-values-5/#attr-notation) — например, для псевдоселектора `::before`. Пример ниже отображает номер заголовка перед текстом заголовка серым цветом:

```css
h1::before {
    color: gray;
    content: attr(data-number) '. ';
}
```

## Колонтитулы {#page-headers}

Специальное правило [`@page`](https://drafts.csswg.org/css-page-3/#page-selector-and-context) описывает стиль каждой страницы печатного документа. Свойство `margin` этого правила определяет отступы, в которых не может быть размещён основной контент страницы, но на этих отступах могут быть размещён дополнительный контент — колонтитулы. Содержимое и стили колонтитулов настраиваются с помощью правил, вложенных в `@page`.

Разные правила соответствуют разным зонам на полях: например, `@top-left-corner` отвечает за зону выше и левее основного контента, а `@top-left` — за зону выше, но не левее. Полный список доступных зон можно посмотреть по ссылке: [Page-Margin Box Definitions](https://drafts.csswg.org/css-page-3/#margin-box-def).

Часто в колонтитулах требуется показывать заголовок текущей главы документа — иными словами, содержимое последнего встреченного заголовка. Это можно сделать с помощью свойств [`string-set`](https://www.w3.org/TR/css-content-3/#string-set) и [`content`](https://www.w3.org/TR/css-content-3/#content-property). Пример ниже демонстрирует это на примере заголовков `<h1>`: при обработке каждого такого заголовка обновляется содержимое строки `current-title` (вы можете использовать другое название строки), а правило `@top-left` подставляет эту строку в верхний левый угол страницы.

```css
@page {
    @top-left {
        content: string(current-title);
    }
}

h1 {
    string-set: current-title content();
}
```

## Нумерация страниц

В любой момент в CSS доступен счётчик [`page`](https://drafts.csswg.org/css-page-3/#page-based-counters), равный номеру текущей страницы PDF-документа. Получить его текущее значение можно через функцию `counter()`. Например, так можно подставить номер страницы в верхний правый [колонтитул](#page-headers):

```css
@page {
    @top-right {
        content: counter(page);
    }
}
```

Помимо значения счётчика в текущем месте документа, существует способ получить значение для места, указанного в атрибуте `href` текущего элемента. Для этого необходимо использовать функцию [`target-counter()`](https://www.w3.org/TR/css-content-3/#target-counter). Например, в момент обработки ссылки в оглавлении можно узнать, какое значение `page` будет там, куда ведёт эта ссылка:

```css
ul.toc a::after {
    content: ' (стр. ' target-counter(attr(href), page) ')';
}
```

## Обложка {#cover}

В стиль любого элемента в документе можно добавить свойство [page](https://drafts.csswg.org/css-page-3/#using-named-pages). Оно позволяет назначить специальный тип той странице, на которой этот элемент находится. К разным типам страниц можно применять разные варианты правила [`@page`](https://drafts.csswg.org/css-page-3/#page-selector-and-context).

Пример ниже указывает, что для страницы, на которой находится элемент с классом `cover-content`, должен быть установлен тип `cover` (вы можете использовать другое название типа). Для этого типа задано фоновое изображение и скрыты колонтитулы.

```css
@page cover {
    background-image: url('cover.png');
 
    @top-left {
        content: none;
    }

    @top-right {
        content: none;
    }
}

.cover-content {
    page: cover;
}
```

## Горизонтальные страницы {#landscape}

Тема, используемая Собиракой по умолчанию, определяет специальный тип страниц `landscape`. Для этого типа включён горизонтальный формат бумаги. Тип применяется к любой странице, на которой находится элемент со свойством `page: landscape`.

```markdown
Работа устройства показана на большой горизонтальной схеме ниже.

`<div style="page: landscape; page-break-after: always"></div>`{=html}

![Большая горизонтальная схема](diagram.png)
```

## Подсветка кода {#highlight}

Поскольку WeasyPrint не поддерживает JavaScript, подсветка блоков кода должна быть реализована во время сборки HTML-содержимого. Собирака реализует её с помощью библиотеки [Pygments](https://pygments.org/), но по умолчанию не подключает соответствующие стили CSS, оставляя это на усмотрение автора темы.

Самый простой способ добавить стиль — выбрать понравившийся на странице [Styles](https://pygments.org/styles/) официального сайта Pygments, а затем локально [сгенерировать необходимый файл CSS](https://pygments.org/docs/cmdline/#generating-styles). Например:

```
pygmentize -f html -S tango > _static/pygments-tango.css
```

Полученный файл укажите в стилях документа обычным способом:

```html
<link rel='stylesheet' href='_static/pygments-tango.css'/>
```