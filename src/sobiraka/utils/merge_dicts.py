def merge_dicts(first: dict, second: dict) -> dict:
    result = {}
    for key in first:
        if key not in second:
            result[key] = first[key]
        else:
            if isinstance(first[key], dict):
                assert isinstance(second[key], dict)
                result[key] = merge_dicts(first[key], second[key])
            else:
                result[key] = second[key]
    for key in second:
        if key not in first:
            result[key] = second[key]
    return result
