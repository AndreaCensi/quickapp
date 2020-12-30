from . import all_args_combinations, comp_comb, all_combinations, Choice


def all_combinations_test1():

    #    samples = [
    #        (all_combinations(1, 2, a=3),
    #         [(1, 2), dict(a=3)]),
    #        (all_combinations(Choice([1, 10]), 2, a=3),
    #         [(1, 2), dict(a=3)],
    #         [(10, 2), dict(a=3)]),
    #    ]
    #
    samples = [
        (
            dict(a=Choice([1, 10]), b=3, c=Choice([3, 4])),
            [
                {"a": 1, "c": 3, "b": 3},
                {"a": 1, "c": 4, "b": 3},
                {"a": 10, "c": 3, "b": 3},
                {"a": 10, "c": 4, "b": 3},
            ],
        ),
        (dict(a=Choice([1, 10]), b=3), [dict(a=1, b=3), dict(a=10, b=3)]),
    ]

    for a, b in samples:

        res = list(all_combinations(a))
        assert res == b


def all_args_combinations_test1():

    for a, b, c in all_args_combinations(1, Choice(["a", "b"]), a=3, b=Choice([1, 2])):
        print a, b, c


def f(p1, p2):
    pass


def comp_comb_test1():
    res = comp_comb(f, Choice([1, 2]), b=Choice([1, 3]))
    print res
