import asyncio
import pickle
import random

from quickapp import QuickApp, QuickAppContext
from .copied_from_compmake_utils import Env, run_with_env
from .quickappbase import run_quickapp


async def f(context: QuickAppContext, name: str):
    await asyncio.sleep(random.uniform(1, 1.4))
    return name + "-done"


def define_jobs_rec(context: QuickAppContext, id_name: str, levels: int, branch: int) -> None:
    if levels == 0:
        context.comp_dynamic(f, id_name)
    else:
        for i in range(branch):
            context.comp_dynamic(define_jobs_rec, f"{id_name}-{i}", levels - 1, branch)


#
#
# def define_jobs2(context: QuickAppContext, id_name: str) -> None:
#     for i in range(2):
#         context.comp_dynamic(define_jobs3, f'{id_name}-{i}')
#
#
# def define_jobs1(context: QuickAppContext, id_name: str) -> None:
#     for i in range(2):
#         context.comp_dynamic(define_jobs2, f'{id_name}-{i}')


class QuickAppDemoChild5(QuickApp):
    def define_options(self, params):
        pass

    async def define_jobs_context(self, sti, context: QuickAppContext):
        context.comp_dynamic(define_jobs_rec, "a", levels=3, branch=2)


@run_with_env
async def test_dynamic4(env: Env) -> None:
    pickle.dumps(f, protocol=pickle.HIGHEST_PROTOCOL)

    await run_quickapp(env, qapp=QuickAppDemoChild5, cmd="rparmake")
    # await env.assert_jobs_equal(
    #     "all",
    #     [
    #         "a-context",
    #         "b-context",
    #         "a-define_jobs1",
    #         "b-define_jobs1",
    #     ],
    # )
    # await env.assert_cmd_success("make *define_jobs1;ls")
    # await env.assert_jobs_equal(
    #     "all",
    #     [
    #         "a-context",
    #         "b-context",
    #         "a-define_jobs1",
    #         "b-define_jobs1",
    #         "a-m-context",
    #         "a-n-context",
    #         "b-m-context",
    #         "b-n-context",
    #         "a-m-define_jobs2",
    #         "b-m-define_jobs2",
    #         "a-n-define_jobs2",
    #         "b-n-define_jobs2",
    #     ],
    # )
    #
    # await env.assert_cmd_success("details a-define_jobs1")
    # await env.assert_defined_by("a-define_jobs1", ["root"])
    #
    # await env.assert_cmd_success("make;ls")
    # await env.assert_jobs_equal(
    #     "all",
    #     [
    #         "a-context",
    #         "b-context",
    #         "a-define_jobs1",
    #         "b-define_jobs1",
    #         "a-m-context",
    #         "a-n-context",
    #         "b-m-context",
    #         "b-n-context",
    #         "a-m-define_jobs2",
    #         "b-m-define_jobs2",
    #         "a-n-define_jobs2",
    #         "b-n-define_jobs2",
    #         "a-m-f",
    #         "a-n-f",
    #         "b-m-f",
    #         "b-n-f",
    #     ],
    # )
    #
    # await env.assert_cmd_success("details a-m-define_jobs2")
    # await env.assert_defined_by("a-m-define_jobs2", ["root", "a-define_jobs1"])
    #
    # await env.assert_cmd_success("details a-m-f")
    # await env.assert_defined_by("a-m-f", ["root", "a-define_jobs1", "a-m-define_jobs2"])
