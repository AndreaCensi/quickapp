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
        names = ["a", "b"]
        for c, id_name in iterate_context_names(context, names):
            c.comp_dynamic(define_jobs1, id_name)


@run_with_env
async def test_dynamic2(env: Env) -> None:
    logger = env.sti.logger
    await run_quickapp(env, qapp=QuickAppDemoChild3, cmd="ls")
    logger.info("ls 1")
    await env.assert_cmd_success("ls not *dynrep*")
    await env.assert_jobs_equal("all", ["a-context", "b-context", "a-define_jobs1", "b-define_jobs1"])
    logger.info("make root")
    await env.assert_cmd_success("make a-define_jobs1 b-define_jobs1")
    logger.info("ls 2")
    await env.assert_cmd_success("ls not *dynrep*")

    await env.assert_jobs_equal(
        "all",
        [
            "a-context",
            "b-context",
            "a-define_jobs1",
            "b-define_jobs1",
            "a-context-0",
            "b-context-0",
            "a-define_jobs2",
            "b-define_jobs2",
        ],
    )
    logger.info("make level1")
    await env.assert_cmd_success("make level1 level2")
    logger.info("ls 3")
    await env.assert_cmd_success("ls not *dynrep*")

    await env.assert_jobs_equal(
        "all",
        [
            "a-context",
            "b-context",
            "a-define_jobs1",
            "b-define_jobs1",
            "a-context-0",
            "b-context-0",
            "a-define_jobs2",
            "b-define_jobs2",
            "a-f",
            "b-f",
        ],
    )
    await env.assert_cmd_success("details a-f")
