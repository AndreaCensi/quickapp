from abc import abstractmethod
from collections import defaultdict
import logging

from contracts import ContractsMeta

from contracts.utils import indent
from compmake.utils import termcolor_colored
from decent_params import UserError
from reprep.utils import deprecated

from .quick_app_base import QuickAppBase


__all__ = ['QuickMultiCmdApp', 'add_subcommand']


    
class QuickMultiCmdApp(QuickAppBase):
    
    def define_program_options(self, params):
        self.define_multicmd_options(params)
        params.accept_extra()
        
    @abstractmethod
    def define_multicmd_options(self, params):
        pass
    
    @abstractmethod
    def initial_setup(self):
        pass

    @classmethod
    def get_usage(cls):
        names = cls._get_subs_names()
        commands = ' | '.join(names)
        return '%prog ' + '[--config DIR1:DIR2:...] {%s} [command options]' % commands
    
    @classmethod
    def get_sub(appcls):
        """ Returns the subclass for the subcommands """
        # mainly because eclipse does not see ".sub" as valid.
        if not hasattr(appcls, 'sub'):
            class Register(ContractsMeta):
                def __init__(cls, clsname, bases, clsdict):  # @UnusedVariable @NoSelf
                    ContractsMeta.__init__(cls, clsname, bases, clsdict)
                    if not 'cmd' in clsdict:
                        # print('skpping %r' % cls)
                        return
                    # print('Automatically registering %s>%s' % (cls, clsname))
                    if clsname in  ['SubCmd']:
                        return
                    cmds = QuickMultiCmdApp.subs[appcls]
                    cmds.append(cls)

            class SubCmd(QuickAppBase):
                __metaclass__ = Register
                
            appcls.sub = SubCmd
        return appcls.sub
    
    def go(self):
        self.initial_setup()
        
        cmds = self._get_subs_as_dict()
        if not cmds:
            msg = 'No commands defined.'
            raise ValueError(msg) 

        extra = self.get_options().get_extra()        
        if not extra:
            msg = 'Please specify as a command one of %s.' % self._get_subs_names_fmt()
            raise UserError(msg)  # XXX: use better exception
        
        cmd_name = extra[0]
        cmd_args = extra[1:]
        if not cmd_name in cmds:
            msg = ('Could not find command %s; please use one of %s.' % 
                   (cmd_name, self._get_subs_names_fmt()))
            raise UserError(msg)
        
        sub = cmds[cmd_name]
        
        sub_inst = sub()
        assert isinstance(sub_inst, QuickAppBase)
        logger_name = '%s-%s' % (self.get_prog_name(), cmd_name)
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        sub_inst.logger = logger
        
        sub_inst.main(args=cmd_args, parent=self)
        
    @classmethod
    def get_epilog(cls):
        subs = cls._get_subs()
        if not subs:
            return 'Warning: no commands defined.'
            
        s = "Commands: \n"
        s += cls.get_epilog_commands()             
        return s
    
    
    @classmethod
    def get_epilog_commands(cls):
        s = ""
        
        for sub in cls._get_subs():
            cmd_name = sub.cmd
            # XXX: fixme
            cmd_short = sub.get_short_description()
            
            cmd_name = termcolor_colored(cmd_name, attrs=['bold'])
            s += "  %30s  %s\n" % (cmd_name, cmd_short)
            if issubclass(sub, QuickMultiCmdApp):
                s += '\n'
                s += indent(sub.get_epilog_commands(), ' ' * 7)
                s += '\n'
                 
        return s
    
    
    @classmethod
    def _get_subs_names_fmt(cls):
        """ Returns 'cmd1, cmd2, cmd3; """
        names = cls._get_subs_names()
        possibilities = ', '.join('%r' % x for x in names)
        return possibilities
        
    @classmethod
    def _get_subs_as_dict(cls):
        """ Returns a dict: cmd_name -> cmd """
        return dict([(x.cmd, x) for x in cls._get_subs()])

    @classmethod
    def _get_subs_names(cls):
        return [x.cmd for x in cls._get_subs()]
    
    @classmethod
    def _get_subs(cls):
        return QuickMultiCmdApp.subs[cls]

    # QuickMultiCmdApp subclass -> (list of  QuickAppBase) 
    subs = defaultdict(list)
    
        
@deprecated
def add_subcommand(app, cmd):
    # logger.info('Adding command  %s - %s' % (app.cmd, cmd.cmd))
    # cmd_name = cmd.cmd
    cmds = QuickMultiCmdApp.subs[app]
    #     if cmd_name in cmds:
    #         msg = 'Duplicate sub command %r.' % cmd_name
    #         raise ValueError(msg) 
    #     cmds[cmd_name] = cmd
    cmds.append(cmd)


