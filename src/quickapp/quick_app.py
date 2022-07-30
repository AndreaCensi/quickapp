import os
import shutil
import sys
import traceback
from abc import abstractmethod
from typing import cast, Dict, List, Optional, Union

from compmake import (
    CacheQueryDB,
    CMJobID,
    CommandFailed,
    ContextImp,
    read_rc_files,
    ShellExitRequested,
    StorageFilesystem,
)
from zuper_commons.text import indent
from zuper_params import DecentParams
from zuper_params.utils import UserError, wrap_script_entry_point
from zuper_utils_asyncio import MyAsyncExitStack, SyncTaskInterface
from . import logger, QUICKAPP_COMPUTATION_ERROR
from .compmake_context import context_get_merge_data, QuickAppContext
from .exceptions import QuickAppException
from .quick_app_base import QuickAppBase
from .report_manager import _dynreports_create_index

__all__ = [
    "QuickApp",
    "quickapp_main",
]


class QuickApp(QuickAppBase):
    """Template for an application that uses compmake to define jobs."""

    # Interface to be implemented
    @abstractmethod
    async def define_jobs_context(self, sti: SyncTaskInterface, context) -> None:
        """Define jobs in the current context."""

        raise NotImplementedError(type(self))

    @abstractmethod
    def define_options(self, params: DecentParams) -> None:
        """Define options for the application."""

        raise NotImplementedError(type(self))

    def define_program_options(self, params: DecentParams) -> None:
        self._define_options_compmake(params)
        self.define_options(params)

    def get_qapp_parent(self) -> "Optional[QuickApp]":
        parent = self.parent
        while parent is not None:
            # logger.info('Checking %s' % parent)
            if isinstance(parent, QuickApp):
                return parent
            parent = parent.parent
        return None

    async def go2(self, sti: SyncTaskInterface) -> int:
        sti.logger.info("in go2()")
        # check that if we have a parent who is a quickapp,
        # then use its context
        qapp_parent = self.get_qapp_parent()
        if qapp_parent is not None:
            # self.info('Found parent: %s' % qapp_parent)
            qc = qapp_parent.child_context
            await self.define_jobs_context(sti, qc)
            return 0
        else:
            # self.info('Parent not found')
            pass

        # if False:
        #     import resource
        #     gbs = 5
        #     max_mem = long(gbs * 1000 * 1048576)
        #     resource.setrlimit(resource.RLIMIT_AS, (max_mem, -1))
        #     resource.setrlimit(resource.RLIMIT_DATA, (max_mem, -1))

        options = self.get_options()

        # if self.get_qapp_parent() is None:
        # only do this if somebody didn't do it before
        # if not options.contracts:
        #
        #     msg = "PyContracts disabled for speed. " "Use --contracts to activate."
        #     self.logger.warning(msg)
        #     contracts.disable_all()

        output_dir = options.output

        if options.reset:
            if os.path.exists(output_dir):
                sti.logger.info("Removing output dir", dir=output_dir)
                try:
                    shutil.rmtree(output_dir)
                except OSError as e:
                    # Directory not empty -- common enough on NFS filesystems
                    # print('errno: %r' % e.errno)
                    if e.errno == 39:
                        pass
                    else:
                        raise

        # Compmake storage for results

        if options.db is not None:
            storage = options.db
        else:
            storage = os.path.join(output_dir, "compmake")
        # logger.debug("Creating storage", where=storage, compress=options.compress)
        db = StorageFilesystem(storage, compress=True)
        currently_executing = [cast(CMJobID, "root")]
        # The original Compmake context

        async with MyAsyncExitStack(sti) as AES:
            oc = await AES.init(ContextImp(db=db, currently_executing=currently_executing))
            await oc.init(sti)
            # Our wrapper
            qc = QuickAppContext(cc=oc, parent=None, job_prefix=None, output_dir=output_dir)
            sti.logger.info("reading rc files")
            await read_rc_files(sti, oc)

            original = oc.get_comp_prefix()
            await self.define_jobs_context(sti, qc)
            oc.comp_prefix(original)

            merged = context_get_merge_data(qc)

            # Only create the index job if we have reports defined
            # or some branched context (which might create reports)
            has_reports = len(qc.get_report_manager().allreports) > 0
            has_branched = qc.has_branched()
            if has_reports or has_branched:
                # self.info('Creating reports')
                oc.comp_dynamic(_dynreports_create_index, merged)
            else:
                pass
                # self.info('Not creating reports.')

            ndefined = len(oc.get_jobs_defined_in_this_session())
            if ndefined == 0:
                # self.comp was never called
                msg = "No jobs defined."
                raise ValueError(msg)
            else:
                if options.console:
                    await oc.compmake_console(sti)
                    return 0
                else:
                    cq = CacheQueryDB(oc.get_compmake_db())
                    targets = cq.all_jobs()
                    todo, done, ready = cq.list_todo_targets(targets)

                    if not todo and options.command is None:
                        msg = "Note: there is nothing for me to do. "
                        msg += "\n(Jobs todo: %s done: %s ready: %s)" % (
                            len(todo),
                            len(done),
                            len(ready),
                        )
                        msg += """\
    This application uses a cache system for the results.
    This means that if you call it second time with the same arguments,
     and if you do not change any input, it will not do anything."""
                        self.warn(msg)
                        return 0

                    if options.command is None:
                        command = "make recurse=1"
                    else:
                        command = options.command

                    await read_rc_files(sti, context=oc)
                    try:
                        _ = await oc.batch_command(sti, command)
                        # print('qapp: ret0 = %s'  % ret0)
                    except CommandFailed:
                        # print('qapp: CommandFailed')
                        ret = QUICKAPP_COMPUTATION_ERROR
                    except ShellExitRequested:
                        # print('qapp: ShellExitRequested')
                        ret = 0
                    else:
                        # print('qapp: else ret = 0')
                        ret = 0

                    return ret

    # async def call_recursive(
    #     self,
    #     sti: SyncTaskInterface,
    #     context,
    #     child_name,
    #     cmd_class,
    #     args: Union[Dict[str, object], List[str]],
    #     extra_dep: Optional[List[str]] = None,
    #     add_outdir=None,
    #     add_job_prefix=None,
    #     separate_resource_manager=False,
    #     separate_report_manager=False,
    #     extra_report_keys=None,
    # ):
    #     if extra_dep is None:
    #         extra_dep = []
    #     instance = cmd_class()
    #     instance.set_parent(self)
    #     is_quickapp = isinstance(instance, QuickApp)
    #
    #     try:
    #         # we are already in a context; just define jobs
    #         child_context = context.child(
    #             qapp=instance,
    #             name=child_name,
    #             extra_dep=extra_dep,
    #             add_outdir=add_outdir,
    #             extra_report_keys=extra_report_keys,
    #             separate_resource_manager=separate_resource_manager,
    #             separate_report_manager=separate_report_manager,
    #             add_job_prefix=add_job_prefix,
    #         )  # XXX
    #
    #         if isinstance(args, list):
    #             try:
    #                 instance.set_options_from_args(args)
    #             except SystemExit as e:
    #                 if e.code == 0:
    #                     return 0
    #                 raise
    #         elif isinstance(args, dict):
    #             instance.set_options_from_dict(args)
    #         else:
    #             assert False
    #
    #         if not is_quickapp:
    #             self.child_context = child_context
    #             res = await instance.go2(sti)
    #         else:
    #             instance.context = child_context
    #             res = instance.define_jobs_context(child_context)
    #
    #         # Add his jobs to our list of jobs
    #         context._jobs.update(child_context.all_jobs_dict())
    #         return res
    #
    #     except Exception as e:
    #         msg = "While trying to run  %s\n" % cmd_class.__name__
    #         msg += "with arguments = %s\n" % args
    #         if "_options" in instance.__dict__:
    #             msg += " parsed options: %s\n" % instance.get_options()
    #             msg += " params: %s\n" % instance.get_options().get_params()
    #         if isinstance(e, QuickAppException):
    #             msg += indent(str(e), "> ")
    #         else:
    #             msg += indent(traceback.format_exc(), "> ")
    #         raise QuickAppException(msg)


def quickapp_main(quickapp_class, args: Optional[List[str]] = None, sys_exit: bool = True) -> int:
    """
    Use like this:

        if __name__ == '__main__':
            quickapp_main(MyQuickApp)


    if sys_exit is True, we call sys.exis(ret), otherwise we return the value.

    """
    instance = quickapp_class()
    if args is None:
        args = sys.argv[1:]

    return wrap_script_entry_point(
        instance.main,
        logger,
        exceptions_no_traceback=(UserError, QuickAppException),
        args=args,
        sys_exit=sys_exit,
    )
