# from contracts import contract
from typing import Sequence

from .minimal_name import _context_names_heuristics

__all__ = [
    "iterate_context_names",
    "iterate_context_pairs",
    "iterate_context_triplets",
    "iterate_context_names_pair",
    "iterate_context_names_triplet",
    "iterate_context_names_quartet",
]


def iterate_context_names(context, it1: Sequence, key: str = None):
    """
    Creates child contexts with minimal names.

    Yields tuples of (context, s1)
    """
    # make strings
    values = list(it1)
    if len(values) == 0:
        raise ValueError("Empty iterator: %s" % values)

    # remove '-' and '_'
    names = _context_names_heuristics(values)

    # print('Using names: %s' % names)

    for x, name in zip(values, names):
        e_c = context.child(name)
        if key is not None:
            keys = {key: x}
            e_c.add_extra_report_keys(**keys)
        yield e_c, x


def iterate_context_names_pair(context, it1: Sequence, it2: Sequence, key1: str = None, key2: str = None):
    """
    Yields tuples of (context, s1, s2).
    """
    for cc, x1 in iterate_context_names(context, it1, key=key1):
        for c, x2 in iterate_context_names(cc, it2, key=key2):
            yield c, x1, x2


iterate_context_pairs = iterate_context_names_pair


#           key1='str|None', key2='str|None', key3='str|None')
def iterate_context_names_triplet(
    context,
    it1: Sequence,
    it2: Sequence,
    it3: Sequence,
    key1: str = None,
    key2: str = None,
    key3: str = None,
):
    """
    Yields tuples of (context, s1, s2, s3).
    """
    for c1, x1 in iterate_context_names(context, it1, key=key1):
        for c2, x2 in iterate_context_names(c1, it2, key=key2):
            for c3, x3 in iterate_context_names(c2, it3, key=key3):
                yield c3, x1, x2, x3


iterate_context_triplets = iterate_context_names_triplet


def iterate_context_names_quartet(context, it1, it2, it3, it4):
    """
    Yields tuples of (context, s1, s2, s3, s4).
    """
    for c1, x1 in iterate_context_names(context, it1):
        for c2, x2 in iterate_context_names(c1, it2):
            for c3, x3 in iterate_context_names(c2, it3):
                for c4, x4 in iterate_context_names(c3, it4):
                    yield c4, x1, x2, x3, x4


def iterate_context_names_quintuplet(context, it1, it2, it3, it4, it5):
    """
    Yields tuples of (context, s1, s2, s3, s4).
    """
    for c1, x1 in iterate_context_names(context, it1):
        for c2, x2 in iterate_context_names(c1, it2):
            for c3, x3 in iterate_context_names(c2, it3):
                for c4, x4 in iterate_context_names(c3, it4):
                    for c5, x5 in iterate_context_names(c4, it5):
                        yield c5, x1, x2, x3, x4, x5
