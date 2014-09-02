from .compmake_context import CompmakeContext, context_get_merge_data
from .exceptions import QuickAppException
from .quick_app_base import QuickAppBase
from .report_manager import _dynreports_create_index
from abc import abstractmethod
from compmake import CommandFailed, StorageFilesystem, read_rc_files
from contracts import ContractsMeta, contract, indent
from decent_params.utils import UserError, wrap_script_entry_point
from quickapp import QUICKAPP_COMPUTATION_ERROR, logger
import contracts
import os
import sys
import traceback

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
        pass

    @abstractmethod
    def define_options(self, params):
        """ Define options for the application. """
        pass

    # Implementation
             
    def _define_options_compmake(self, params):
        script_name = self.get_prog_name()
        default_output_dir = 'out-%s/' % script_name

        g = 'Generic arguments for Quickapp'
        # TODO: use  add_help=False to ARgParsre
        # params.add_flag('help', short='-h', help='Shows help message')
        params.add_flag('contracts', help='Activate PyContracts', group=g)
        params.add_flag('profile', help='Use Python Profiler', group=g)
        params.add_string('output', short='o',
                          help='Output directory',
                                    default=default_output_dir, group=g)
    
        params.add_flag('console', help='Use Compmake console', group=g)

        params.add_string('command', short='c',
                      help="Command to pass to compmake for batch mode",
                      default='make recurse=1', group=g)
    
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
            context = qapp_parent.child_context  
            self.define_jobs_context(context)
            return
        else:
            # self.info('Parent not found')
            pass
            

        if False:            
            import resource
            gbs = 5
            max_mem = long(gbs * 1000 * 1048576L)
            resource.setrlimit(resource.RLIMIT_AS, (max_mem, -1))
            resource.setrlimit(resource.RLIMIT_DATA, (max_mem, -1))

        options = self.get_options()
        
        if self.get_qapp_parent() is None:
            # only do this if somebody didn't do it before
            if not options.contracts:
                msg = 'PyContracts disabled for speed. Use --contracts to activate.'
                self.logger.warning(msg)
                contracts.disable_all()

        output_dir = options.output
        
        # Compmake storage for results        
        storage = os.path.join(output_dir, 'compmake')
        db = StorageFilesystem(storage, compress=True)
        currently_executing = ['root']
        context = CompmakeContext(db=db, currently_executing=currently_executing,
                                  parent=None, qapp=self, job_prefix=None,
                                  output_dir=output_dir)
        read_rc_files(context)
        
        self.context = context
        original = self.context.get_comp_prefix()
        self.define_jobs_context(context)
        self.context.comp_prefix(original)
        
        merged  = context_get_merge_data(context)
    
        # Only create the index job if we have reports defined
        # or some branched context (which might create reports)
        has_reports = len(context.get_report_manager().allreports) > 0
        has_branched = context.has_branched()
        if has_reports or has_branched:
            self.info('Creating reports')
            from compmake import Context
            Context.comp_dynamic(context, _dynreports_create_index, merged)
        else:
            self.info('Not creating reports.')
        
        if context.n_comp_invocations == 0:
            # self.comp was never called
            msg = 'No jobs defined.'
            raise ValueError(msg)
        else: 
            if not options.console:
                try: 
                    self.context.batch_command(options.command)
                except CommandFailed:
                    ret = QUICKAPP_COMPUTATION_ERROR
                else:
                    ret = 0
                     
                return ret
            else:
                self.context.compmake_console()
                return 0

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
                msg += indent(traceback.format_exc(e), '> ')
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


