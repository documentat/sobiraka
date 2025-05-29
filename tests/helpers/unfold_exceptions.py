def unfold_exception_types(eg: BaseException) -> set[type[BaseException]]:
    if isinstance(eg, BaseExceptionGroup):
        result: set[type[BaseException]] = set()
        for e in eg.exceptions:
            result |= unfold_exception_types(e)
        return result

    return {type(eg)}
