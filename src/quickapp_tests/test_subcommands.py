#!/usr/bin/env python3

from quickapp import QuickMultiCmdApp
from zuper_commons.test_utils import known_failure
from zuper_params import DecentParams
from .copied_from_compmake_utils import Env, run_with_env
from .quickappbase import run_quickapp


class DemoApp(QuickMultiCmdApp):
    cmd = "dp"

    def define_multicmd_options(self, params: DecentParams):
        params.add_string("config", help="Config Joint")
        params.add_int("second", help="Second parameter")

    def initial_setup(self):
        options = self.get_options()
        self.info("Loading configuration", config=options.config)
        self.info(param2=options.param2)


class DemoAppCmd1(DemoApp.get_sub()):
    cmd = "cmd1"
    short = "First command"

    def define_options(self, params: DecentParams):
        params.add_int("param1", help="First parameter", default=1)
        params.add_int("param2", help="Second parameter")

    def define_jobs(self):
        options = self.get_options()
        self.info("My param2 is %r." % options.param2)


class DemoAppCmd2(DemoApp.get_sub()):
    cmd = "cmd2"
    short = "Second command"

    def define_options(self, params):
        params.add_int("param1", help="First parameter", default=1)

    def define_jobs(self):
        pass


@known_failure
@run_with_env
async def test_subcommands(env: Env) -> None:
    args = [
        "-c",
        "make all",
        "--config",
        "abd",
        "--second",
        "3",
        "cmd1",
        "--param1",
        "10",
        "--param2",
        "42",
    ]
    await run_quickapp(env, DemoApp, args)


#
# if __name__ == '__main__':
#     quickapp_main(DemoApp)
#
