#!/usr/bin/env python3

from quickapp import iterate_context_names, QuickApp
from reprep import Report
from .copied_from_compmake_utils import Env, run_with_env
from .quickappbase import run_quickapp


def report_example1(param1, param2):
    r = Report()
    r.text("type", "This is one report")
    r.text("param1", "%s" % param1)
    r.text("param2", "%s" % param2)
    return r


def report_example2(param1, param2):
    r = Report()
    r.text("type", "This is another report")
    r.text("param1", "%s" % param1)
    r.text("param2", "%s" % param2)
    return r


def instance_reports1(context):
    param1s = ["a", "b"]
    for c1, param1 in iterate_context_names(context, param1s, key="param1"):
        c1.comp_dynamic(instance_reports2, param1=param1)


def instance_reports2(context, param1):
    param2s = [1, 2]
    for c2, param2 in iterate_context_names(context, param2s, key="param2"):
        c2.comp_dynamic(instance_reports3, param1=param1, param2=param2)


def instance_reports3(context, param1, param2):
    context.comp(dummy)

    r = context.comp(report_example2, param1=param1, param2=param2)
    context.add_report(r, "report_example2")

    context.comp_dynamic(instance_reports4, param1=param1, param2=param2)


def instance_reports4(context, param1, param2):
    r = context.comp(report_example1, param1=param1, param2=param2)
    context.add_report(r, "report_example1")


def dummy():
    pass


class QuickAppDemoReport2(QuickApp):
    def define_options(self, params):
        pass

    async def define_jobs_context(self, sti, context):
        context.comp_dynamic(instance_reports1)


@run_with_env
async def test_rec_rep2(env: Env) -> None:
    await run_quickapp(env, QuickAppDemoReport2, cmd="make recurse=1")


if __name__ == "__main__":
    main = QuickAppDemoReport2.get_sys_main()
    main()
