import sys

from sobiraka.models import Book


def print_errors(book: Book) -> bool:
    errors_found: bool = False
    for page in book.pages:
        if page.errors:
            message = f'Errors in {page.relative_path}:'
            errors = sorted(page.errors, key=lambda e: (e.__class__.__name__, e))
            for error in errors:
                message += f'\n    {error}'
            message += '\n'
            print(message, file=sys.stderr)
            errors_found = True
    return errors_found
