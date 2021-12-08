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


class QuickAppDemoReport(QuickApp):
    def define_options(self, params):
        pass

    async def define_jobs_context(self, sti, context):
        param1s = ["a", "b"]
        param2s = [1, 2]

        for c1, param1 in iterate_context_names(context, param1s):
            c1.add_extra_report_keys(param1=param1)
            for c2, param2 in iterate_context_names(c1, param2s):
                c2.add_extra_report_keys(param2=param2)
                r = c2.comp(report_example1, param1=param1, param2=param2)
                c2.add_report(r, "report_example1")
                r = c2.comp(report_example2, param1=param1, param2=param2)
                c2.add_report(r, "report_example2")


@run_with_env
async def test_order(env: Env) -> None:
    logger = env.sti.logger
    await run_quickapp(env, QuickAppDemoReport, cmd="ls")
    logger.info("---- now make")
    await env.assert_cmd_success("make")
    logger.info("---- result of first make")
    await env.assert_cmd_success("ls")
    logger.info("---- result of remake")
    await env.assert_cmd_success("ls")
    await env.assert_cmd_success("make")
    await env.assert_cmd_success("ls")


#         self.assert_cmd_success('make')
