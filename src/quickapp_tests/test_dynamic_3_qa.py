from quickapp import iterate_context_names, QuickApp
from .copied_from_compmake_utils import Env, run_with_env
from .quickappbase import run_quickapp


def f(name):
    print(name)
    return name


def define_jobs2(context, id_name):
    context.comp(f, id_name)


def define_jobs1(context, id_name):
    context.comp_dynamic(define_jobs2, id_name)


class QuickAppDemoChild3(QuickApp):
    def define_options(self, params):
        pass

    async def define_jobs_context(self, sti, context):
        names1 = ["a", "b"]
        names2 = ["m", "n"]
        for c1, name1 in iterate_context_names(context, names1):
            for c2, name2 in iterate_context_names(c1, names2):
                c2.comp_dynamic(define_jobs1, name1 + name2)


@run_with_env
async def test_dynamic3(env: Env):
    await run_quickapp(env, qapp=QuickAppDemoChild3, cmd="ls")

    await env.assert_cmd_success("check_consistency")

    await env.assert_jobs_equal(
        "all",
        [
            "a-m-context",
            "a-n-context",
            "b-m-context",
            "b-n-context",
            "a-m-define_jobs1",
            "b-m-define_jobs1",
            "a-n-define_jobs1",
            "b-n-define_jobs1",
        ],
    )
    await env.assert_cmd_success("make *-define_jobs1")

    await env.assert_cmd_success("ls")
    await env.assert_jobs_equal(
        "all",
        [
            "a-m-context",
            "a-n-context",
            "b-m-context",
            "b-n-context",
            "a-m-define_jobs1",
            "b-m-define_jobs1",
            "a-n-define_jobs1",
            "b-n-define_jobs1",
            "b-m-context-0",
            "a-n-context-0",
            "a-m-context-0",
            "b-n-context-0",
            "a-m-define_jobs2",
            "b-m-define_jobs2",
            "a-n-define_jobs2",
            "b-n-define_jobs2",
        ],
    )
    await env.assert_cmd_success("make;ls")
    await env.assert_jobs_equal(
        "all",
        [
            "a-m-context",
            "a-n-context",
            "b-m-context",
            "b-n-context",
            "a-m-define_jobs1",
            "b-m-define_jobs1",
            "a-n-define_jobs1",
            "b-n-define_jobs1",
            "b-m-context-0",
            "a-n-context-0",
            "a-m-context-0",
            "b-n-context-0",
            "a-m-define_jobs2",
            "b-m-define_jobs2",
            "a-n-define_jobs2",
            "b-n-define_jobs2",
            "a-m-f",
            "a-n-f",
            "b-m-f",
            "b-n-f",
        ],
    )
    await env.assert_cmd_success("details a-m-f")
    await env.assert_defined_by("a-m-f", ["root", "a-m-define_jobs1", "a-m-define_jobs2"])
