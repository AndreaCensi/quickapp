#!/usr/bin/env python3
from nose.tools import assert_equal

from compmake_tests.utils import Env, run_with_env
from quickapp import CompmakeContext, iterate_context_names, QuickApp
from quickapp_tests.quickappbase import run_quickapp


def f(name):
    print(name)
    return name


def define_jobs(context, id_name):
    assert isinstance(context, CompmakeContext)
    context.comp(f, id_name)


class QuickAppDemoChild(QuickApp):
    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        names = ["a", "b", "c"]
        for c, id_name in iterate_context_names(context, names):
            define_jobs(c, id_name)


@run_with_env
async def test_dynamic(env: Env):
    ret_found = await run_quickapp(env, QuickAppDemoChild, "make")
    assert not ret_found, ret_found

    # print('jobs in %s: %s' % (await env.db, list(all_jobs(await env.db))))
    await env.assert_jobs_equal("all", ["a-f", "b-f", "c-f"])


class QuickAppDemoChild2(QuickApp):
    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        names = ["a", "b", "c"]
        for c, id_name in iterate_context_names(context, names):
            c.comp_dynamic(define_jobs, id_name)


@run_with_env
async def test_child_(env: Env):
    await run_quickapp(env, qapp=QuickAppDemoChild2, cmd="ls")

    # These are the jobs currently defined
    await env.assert_jobs_equal(
        "all",
        [
            "a-define_jobs",
            "b-define_jobs",
            "c-define_jobs",
            "a-context",
            "b-context",
            "c-context",
        ],
    )

    await env.assert_cmd_success("make *-define_jobs; ls")

    await env.assert_jobs_equal(
        "all",
        [
            "a-define_jobs",
            "b-define_jobs",
            "c-define_jobs",
            "a-context",
            "b-context",
            "c-context",
            "a-f",
            "b-f",
            "c-f",
        ],
    )

    await env.assert_jobs_equal(
        "done",
        [
            "a-define_jobs",
            "b-define_jobs",
            "c-define_jobs",
            "a-context",
            "b-context",
            "c-context",
        ],
    )

    await env.assert_cmd_success("make; ls")

    await env.assert_jobs_equal(
        "done",
        [
            "a-define_jobs",
            "b-define_jobs",
            "c-define_jobs",
            "a-context",
            "b-context",
            "c-context",
            "a-f",
            "b-f",
            "c-f",
        ],
    )
