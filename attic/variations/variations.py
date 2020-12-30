import itertools
from compmake import comp
from reprep.report_utils import StoreResults


def all_combinations(params, give_choices=False):
    choices = sorted([k for k in params if isinstance(params[k], Choice)])
    values = [list(params[k]) for k in choices]
    others = dict([(a, b) for a, b in params.items() if a not in choices])
    for x in itertools.product(*values):
        chosen = dict(zip(choices, x))
        res = dict(chosen)
        res.update(others)
        if give_choices:
            yield res, chosen
        else:
            yield res


def all_args_combinations(*args, **kwargs):
    for i, a in enumerate(args):
        kwargs[str(i)] = a

    for c, chosen in all_combinations(kwargs, True):
        margs = []
        for i in range(len(args)):
            margs.append(c[str(i)])
            del c[str(i)]

        yield tuple(margs), c, chosen


def call_comb(function, *args, **kwargs):
    sr = StoreResults()
    for a, b, chosen in all_args_combinations(*args, **kwargs):
        sr[chosen] = function(*a, **b)
    return sr


def comp_comb(function, *args, **kwargs):
    sr = StoreResults()
    for a, b, chosen in all_args_combinations(*args, **kwargs):

        def s(k):
            return ""
            if isinstance(k, int):
                return ""
            else:
                return str(k)

        pid = "-".join(["%s%s" % (s(k), v) for k, v in chosen.items()])
        job_id = "%s-%s" % (function.__name__, pid)
        b["job_id"] = job_id
        job = comp(function, *a, **b)
        sr[chosen] = job
    return sr
