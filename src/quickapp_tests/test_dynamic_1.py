from compmake import Context
from quickapp import DecentParams, QuickApp, QuickAppContext
from zuper_commons.test_utils import my_assert_equal
from .copied_from_compmake_utils import Env, run_with_env
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

    async def define_jobs_context(self, sti, context: QuickAppContext):
        context.comp_dynamic(define_jobs1)


@run_with_env
async def test_dynamic1(env: Env) -> None:
    await run_quickapp(env, qapp=QuickAppDemoChild1, cmd="ls")
    defined = await env.all_jobs()
    my_assert_equal(
        {
            "define_jobs1",
            "_dynreports_create_index",
            "_dynreports_getbra",
            "_dynreports_getres",
            "_dynreports_merge",
            "context",
        },
        set(defined),
    )
    env.sti.logger.info(defined=defined)
    await env.assert_cmd_success("make define_jobs1")
    await env.assert_cmd_success("ls")

    await env.assert_cmd_success("make")
    await env.assert_cmd_success("make")
    await env.assert_cmd_success("make")
