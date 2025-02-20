def autoprefix(lang: str, codename: str) -> str | None:
    return '/'.join(filter(None, (lang, codename))) or None
