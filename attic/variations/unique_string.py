def all_starts_with(values, c):
    return all([x[0] == c for x in values])


def all_end_with(values, c):
    return all([x[-1] == c for x in values])


def remove_common_prefix(values):
    while True:
        c = values[0][0]
        if all_starts_with(values, c):
            values = [x[1:] for x in values]
        else:
            break
    return values


def remove_common_suffix(values):
    while True:
        c = values[0][-1]
        if all_end_with(values, c):
            values = [x[:-1] for x in values]
        else:
            break
    return values


def get_compact_unique_strings(values):
    """ Returns unique strings for each value """
    v = map(str, list(values))

    def sanitize(s):
        s = s.replace(".", "")
        s = s.replace("/", "_")

    v = map(sanitize, v)

    if isinstance(values[0], str):
        values = remove_common_prefix(values)
        values = remove_common_suffix(values)

    return dict(zip(values, v))
