# Манифест проекта

<blockquote class='book-hint warning'>
Документация по формату манифеста пока не написана.

Но если ваш любимый редактор поддерживает работу с JSON Schema, то подключите файл `sobiraka-project.yaml` из исходников Собираки — вам станет чуть удобнее писать манифесты.
</blockquote>

## Поля

### primary

## Примеры

### Простой проект

```yaml
title: Documentation
paths:
  root: src/en
  include: [one, two, three]
html:
  resources_prefix: img
```

### Сложный проект

```yaml
primary: ru/vol1
languages:
  en:
    volumes:
      vol1:
        title: Documentation
        paths:
          root: src/en
          include: [one, two, three]
        html:
          resources_prefix: img
      vol2:
        title: Documentation
        paths:
          root: src/en
          include: [four, five, six]
        html:
          resources_prefix: img
  ru:
    volumes:
      vol1:
        title: Документация
        paths:
          root: src/ru
          include: [one, two, three]
        html:
          resources_prefix: img
      vol2:
        title: Документация
        paths:
          root: src/ru
          include: [four, five, six]
        html:
          resources_prefix: img
```
