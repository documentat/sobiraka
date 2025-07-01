from sobiraka.utils import AbsolutePath


def first_existing_path(*paths: AbsolutePath) -> AbsolutePath | None:
    for path in paths:
        if path.exists():
            return path
    return None
