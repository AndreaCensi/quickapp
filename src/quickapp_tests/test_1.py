#!/usr/bin/env python3
import os
from shutil import rmtree
from tempfile import mkdtemp
from typing import List

from nose.tools import assert_equal

from compmake_tests.utils import Env, run_with_env
from quickapp import QuickApp, QUICKAPP_COMPUTATION_ERROR, QUICKAPP_USER_ERROR
from reprep import Report
from zuper_commons.cmds import ExitCode
from zuper_commons.types import ZAssertionError
from .quickappbase import run_quickapp


def actual_computation(param1, param2):
    print("computing (%s %s)" % (param1, param2))
    return [1, 2, 3, 4]


def report_example(param2, samples):
    print("report_example(%s, %s)" % (param2, samples))
    if param2 == -1:
        print("generating exception")
        raise Exception("fake exception")
    r = Report()
    r.text("samples", str(samples))
    print("creating report")
    return r


class QuickAppDemo2(QuickApp):
    description = "QuickAppDemo2"
    cmd = "quick-app-demo"

    def define_options(self, params):
        params.add_int("param1", help="First parameter", default=1)
        params.add_int("param2", help="Second parameter")

    def define_jobs_context(self, context):
        options = self.get_options()
        param1 = options.param1
        param2 = options.param2
        samples = context.comp(actual_computation, param1=param1, param2=param2)

        rj = context.comp(report_example, param2, samples)
        context.add_report(rj, "report_example")


@run_with_env
async def test_compapp(env: Env):
    cases = []

    def add(args0: List[str], ret0: ExitCode):
        cases.append(dict(args=args0, ret=ret0))

    add(
        ["--compress", "-c", "clean;make", "--param1", "10", "--param2", "1"],
        ExitCode.OK,
    )

    # parse error
    add(
        ["--compress", "-c", "clean;make", "--param1", "10", "--parm2", "1"],
        ExitCode.WRONG_ARGUMENTS,
    )

    # computation exception
    add(
        ["--compress", "-c", "clean;make", "--param1", "10", "--param2", "-1"],
        QUICKAPP_COMPUTATION_ERROR,
    )

    for c in cases:
        args = c["args"]

        if isinstance(args, str):
            args = args.split()
        tmpdir = mkdtemp()
        ret = c["ret"]
        with open(os.path.join(tmpdir, ".compmake.rc"), "w") as f:
            f.write("config echo 1\n")
        ret_found = await run_quickapp(env, QuickAppDemo2, args, return_retcode=True)
        different = (not (ret_found in [0, None]) and (ret in [0, None])) and (ret_found != ret)
        if different:
            raise ZAssertionError(expected=ret, fount=ret, c=c)
        # msg = f"Expected {ret!r}, got {ret_found!r}.\nArguments: {c['args']} "
        # assert_equal(ret, ret_found, msg)
        rmtree(tmpdir)


#
# if __name__ == '__main__':
#     quickapp_main(QuickAppDemo2)
#
