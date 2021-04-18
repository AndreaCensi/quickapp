from typing import List, Type, Union

from nose.tools import assert_equal

from .copied_from_compmake_utils import Env
from quickapp import QuickAppBase
from zuper_commons.types import ZTypeError


async def run_quickapp(
    env: Env,
    qapp: Type[QuickAppBase],
    cmd: Union[str, List[str]],
    return_retcode: bool = False,
):
    if isinstance(cmd, str):
        # if ' ' in cmd:
        #     raise ZValueError('pass a list', cmd=cmd)
        args = ["-o", env.rootd + "/out", "--db", env.rootd, "-c", cmd, "--compress"]
    elif isinstance(cmd, list):
        args = ["-o", env.rootd + "/out", "--db", env.rootd, "--compress"] + cmd
    else:
        raise ZTypeError(cmd=cmd)
    instance = qapp()
    env.sti.logger.info("run_quickapp", args=args)
    retcode = await instance.main(env.sti, args=args)

    # tell the context that it's all good
    jobs = await env.all_jobs()
    await env.cc.reset_jobs_defined_in_this_session(jobs)

    if return_retcode:
        return retcode
    else:
        assert_equal(0, retcode)
