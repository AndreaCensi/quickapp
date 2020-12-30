from nose.tools import assert_equal

from compmake import Context
from compmake_tests.utils import Env, run_with_env
from decent_params import DecentParams
from quickapp import QuickApp, QuickAppContext
from .quickappbase import run_quickapp


def f():
    return 1


def define_jobs2(context: Context):
    context.comp(f)


def define_jobs1(context: Context):
    context.comp_dynamic(define_jobs2)


class QuickAppDemoChild1(QuickApp):
    def define_options(self, params: DecentParams):
        pass

    def define_jobs_context(self, context: QuickAppContext):
        context.comp_dynamic(define_jobs1)


@run_with_env
async def test_dynamic1(env: Env):
    await run_quickapp(env, qapp=QuickAppDemoChild1, cmd="ls")
    defined = await env.all_jobs()
    assert_equal(
        set(defined),
        {
            "define_jobs1",
            "_dynreports_create_index",
            "_dynreports_getbra",
            "_dynreports_getres",
            "_dynreports_merge",
            "context",
        },
    )
    env.sti.logger.info(defined=defined)
    await env.assert_cmd_success("make define_jobs1")
    await env.assert_cmd_success("ls")

    await env.assert_cmd_success("make")
    await env.assert_cmd_success("make")
    await env.assert_cmd_success("make")
