import os
import shutil
import sys
import traceback
from abc import abstractmethod

import contracts
from compmake import CommandFailed, StorageFilesystem, read_rc_files
from compmake.context import Context
from compmake.exceptions import ShellExitRequested
from compmake.jobs.uptodate import CacheQueryDB
from contracts import ContractsMeta, contract, indent
from decent_params.utils import UserError, wrap_script_entry_point
from quickapp import QUICKAPP_COMPUTATION_ERROR, logger

from .compmake_context import CompmakeContext, context_get_merge_data
from .exceptions import QuickAppException
from .quick_app_base import QuickAppBase
from .report_manager import _dynreports_create_index

__all__ = [
    'QuickApp',
    'quickapp_main',
]


class QuickApp(QuickAppBase):
    """ Template for an application that uses compmake to define jobs. """

    __metaclass__ = ContractsMeta

    # Interface to be implemented
    @abstractmethod
    def define_jobs_context(self, context):
        """ Define jobs in the current context. """

    @abstractmethod
    def define_options(self, params):
        """ Define options for the application. """

    # Implementation

    def _define_options_compmake(self, params):
        script_name = self.get_prog_name()
        s = script_name
        s = s.replace('.py', '')
        s = s.replace(' ', '_')
        default_output_dir = 'out-%s/' % s

        g = 'Generic arguments for Quickapp'
        # TODO: use  add_help=False to ARgParsre
        # params.add_flag('help', short='-h', help='Shows help message')
        params.add_flag('contracts', help='Activate PyContracts', group=g)
        params.add_flag('profile', help='Use Python Profiler', group=g)
        params.add_flag('compress', help='Compress stored data', group=g)
        params.add_string('output', short='o',
                          help='Output directory',
                          default=default_output_dir, group=g)

        params.add_flag('reset', help='Deletes the output directory', group=g)
        # params.add_flag('compmake', help='Activates compmake caching (if app is such that set_default_reset())', group=g)

        params.add_flag('console', help='Use Compmake console', group=g)

        params.add_string('command', short='c',
                          help="Command to pass to compmake for batch mode",
                          default=None, group=g)

    def define_program_options(self, params):
        self._define_options_compmake(params)
        self.define_options(params)

    def get_qapp_parent(self):
        parent = self.parent
        while parent is not None:
            # logger.info('Checking %s' % parent)
            if isinstance(parent, QuickApp):
                return parent
            parent = parent.parent
        return None

    def go(self):
        # check that if we have a parent who is a quickapp,
        # then use its context
        qapp_parent = self.get_qapp_parent()
        if qapp_parent is not None:
            # self.info('Found parent: %s' % qapp_parent)
            qc = qapp_parent.child_context
            self.define_jobs_context(qc)
            return
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

        if self.get_qapp_parent() is None:
            # only do this if somebody didn't do it before
            if not options.contracts:
                msg = ('PyContracts disabled for speed. '
                       'Use --contracts to activate.')
                self.logger.warning(msg)
                contracts.disable_all()

        output_dir = options.output

        if options.reset:
            if os.path.exists(output_dir):
                self.logger.info('Removing output dir %r.' % output_dir)
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
        storage = os.path.join(output_dir, 'compmake')
        print('Creating storage in %s with compress %s' % (storage, options.compress))
        db = StorageFilesystem(storage, compress=options.compress)
        currently_executing = ['root']
        # The original Compmake context
        oc = Context(db=db, currently_executing=currently_executing)
        # Our wrapper
        qc = CompmakeContext(cc=oc,
                             parent=None, qapp=self, job_prefix=None,
                             output_dir=output_dir)
        read_rc_files(oc)

        original = oc.get_comp_prefix()
        self.define_jobs_context(qc)
        oc.comp_prefix(original)

        merged = context_get_merge_data(qc)

        # Only create the index job if we have reports defined
        # or some branched context (which might create reports)
        has_reports = len(qc.get_report_manager().allreports) > 0
        has_branched = qc.has_branched()
        if has_reports or has_branched:
            self.info('Creating reports')
            oc.comp_dynamic(_dynreports_create_index, merged)
        else:
            self.info('Not creating reports.')

        ndefined = len(oc.get_jobs_defined_in_this_session())
        if ndefined == 0:
            # self.comp was never called
            msg = 'No jobs defined.'
            raise ValueError(msg)
        else:
            if options.console:
                oc.compmake_console()
                return 0
            else:
                cq = CacheQueryDB(oc.get_compmake_db())
                targets = cq.all_jobs()
                todo, done, ready = cq.list_todo_targets(targets)

                if not todo:
                    msg = "Note: there is nothing for me to do. "
                    msg += '\n(Jobs todo: %s done: %s ready: %s)' % (len(todo), len(done), len(ready))
                    msg += '\nThis application uses a cache system (Compmake) for the results.'
                    msg += '\nThis means that if you call it second time with the same arguments it will not do anything.'
                    msg += '\n'
                    msg += '\nTo force re-doing of everything, use the option --reset.'
                    msg += '\n'
                    msg += '\nTo inspect what was already done, use the option --console.'
                    self.warn(msg)
                    return 0

                if options.command is None:
                    command = 'make recurse=1'
                else:
                    command = options.command

                try:
                    _ = oc.batch_command(command)
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

    @contract(args='dict(str:*)|list(str)', extra_dep='list')
    def call_recursive(self, context, child_name, cmd_class, args,
                       extra_dep=[],
                       add_outdir=None,
                       add_job_prefix=None,
                       separate_resource_manager=False,
                       separate_report_manager=False,
                       extra_report_keys=None):
        instance = cmd_class()
        instance.set_parent(self)
        is_quickapp = isinstance(instance, QuickApp)

        try:
            # we are already in a context; just define jobs
            child_context = context.child(qapp=instance, name=child_name,
                                          extra_dep=extra_dep,
                                          add_outdir=add_outdir,
                                          extra_report_keys=extra_report_keys,
                                          separate_resource_manager=separate_resource_manager,
                                          separate_report_manager=separate_report_manager,
                                          add_job_prefix=add_job_prefix)  # XXX

            if isinstance(args, list):
                instance.set_options_from_args(args)
            elif isinstance(args, dict):
                instance.set_options_from_dict(args)
            else:
                assert False

            if not is_quickapp:
                self.child_context = child_context
                res = instance.go()
            else:
                instance.context = child_context
                res = instance.define_jobs_context(child_context)

            # Add his jobs to our list of jobs
            context._jobs.update(child_context.all_jobs_dict())
            return res

        except Exception as e:
            msg = 'While trying to run  %s\n' % cmd_class.__name__
            msg += 'with arguments = %s\n' % args
            if '_options' in instance.__dict__:
                msg += ' parsed options: %s\n' % instance.get_options()
                msg += ' params: %s\n' % instance.get_options().get_params()
            if isinstance(e, QuickAppException):
                msg += indent(str(e), '> ')
            else:
                msg += indent(traceback.format_exc(), '> ')
            raise QuickAppException(msg)


def quickapp_main(quickapp_class, args=None, sys_exit=True):
    """
        Use like this:

            if __name__ == '__main__':
                quickapp_main(MyQuickApp)


        if sys_exit is True, we call sys.exis(ret), otherwise we return the value.

    """
    instance = quickapp_class()
    if args is None:
        args = sys.argv[1:]

    return wrap_script_entry_point(instance.main, logger,
                                   exceptions_no_traceback=(UserError, QuickAppException),
                                   args=args, sys_exit=sys_exit)
