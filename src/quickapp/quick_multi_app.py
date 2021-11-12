import logging
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Type

from conf_tools.utils import indent, termcolor_colored
from zuper_params import DecentParams, UserError
from zuper_utils_asyncio import SyncTaskInterface
from .quick_app_base import QuickAppBase

__all__ = ["QuickMultiCmdApp", "add_subcommand"]


class QuickMultiCmdApp(QuickAppBase):
    sub: "Type[QuickAppBase]"

    def define_program_options(self, params: DecentParams):
        self._define_options_compmake(params)
        self.define_multicmd_options(params)
        params.accept_extra()
        params.subcommands = True

    @abstractmethod
    def define_multicmd_options(self, params: DecentParams):
        pass

    @abstractmethod
    def initial_setup(self):
        pass

    @classmethod
    def get_usage(cls):
        names = cls._get_subs_names()
        commands = " | ".join(names)
        return "%prog " + "[--config DIR1:DIR2:...] {%s} [command options]" % commands

    # noinspection PyMethodParameters
    @classmethod
    def get_sub(appcls):
        """Returns the subclass for the subcommands"""
        # mainly because eclipse does not see ".sub" as valid.
        if not hasattr(appcls, "sub"):
            # from contracts import ContractsMeta
            class Register:
                def __init__(self, clsname, bases, clsdict):
                    # ContractsMeta.__init__(cls, clsname, bases, clsdict)
                    if not "cmd" in clsdict:
                        # print('skpping %r' % cls)
                        return
                    # print('Automatically registering %s>%s' % (cls, clsname))
                    if clsname in ["SubCmd"]:
                        return
                    cmds = QuickMultiCmdApp.subs[appcls]
                    cmds.append(self)

            class SubCmd(QuickAppBase, ABC):

                __metaclass__ = Register

            appcls.sub = SubCmd
        return appcls.sub

    async def go2(self, sti: SyncTaskInterface):
        self.initial_setup()

        cmds = self._get_subs_as_dict()
        if not cmds:
            msg = "No commands defined."
            raise ValueError(msg)

        options = self.get_options()
        extra = options.get_extra()
        if not extra:
            msg = "Please specify as a command one of %s." % self._get_subs_names_fmt()
            raise UserError(msg)  # XXX: use better exception

        sys.stderr.write(f"extra = {extra}")
        cmd_name = extra[0]
        cmd_args = extra[1:]
        if not cmd_name in cmds:
            msg = f"Could not find command {cmd_name!r}."
            raise UserError(msg, known=self._get_subs_names_fmt())

        sub = cmds[cmd_name]

        sub_inst = sub()
        assert isinstance(sub_inst, QuickAppBase)
        logger_name = "%s-%s" % (self.get_prog_name(), cmd_name)
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        sub_inst.logger = logger

        self.info("now passing to other", cmd_args=cmd_args)
        return await sub_inst.main(sti, args=cmd_args, parent=self)

    @classmethod
    def get_epilog(cls):
        subs = cls._get_subs()
        if not subs:
            return "Warning: no commands defined."

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

            cmd_name = termcolor_colored(cmd_name, attrs=["bold"])
            s += "  %30s  %s\n" % (cmd_name, cmd_short)
            if issubclass(sub, QuickMultiCmdApp):
                s += "\n"
                s += indent(sub.get_epilog_commands(), " " * 7)
                s += "\n"

        return s

    @classmethod
    def _get_subs_names_fmt(cls):
        """Returns 'cmd1, cmd2, cmd3;"""
        names = cls._get_subs_names()
        possibilities = ", ".join("%r" % x for x in names)
        return possibilities

    @classmethod
    def _get_subs_as_dict(cls):
        """Returns a dict: cmd_name -> cmd"""
        return dict([(x.cmd, x) for x in cls._get_subs()])

    @classmethod
    def _get_subs_names(cls):
        return [x.cmd for x in cls._get_subs()]

    @classmethod
    def _get_subs(cls):
        return QuickMultiCmdApp.subs[cls]

    # QuickMultiCmdApp subclass -> (list of  QuickAppBase)
    subs = defaultdict(list)


# @deprecated
def add_subcommand(app, cmd):
    # logger.info('Adding command  %s - %s' % (app.cmd, cmd.cmd))
    # cmd_name = cmd.cmd
    cmds = QuickMultiCmdApp.subs[app]
    #     if cmd_name in cmds:
    #         msg = 'Duplicate sub command %r.' % cmd_name
    #         raise ValueError(msg)
    #     cmds[cmd_name] = cmd
    cmds.append(cmd)
