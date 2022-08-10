import os
import sys
import traceback
from abc import ABC, abstractmethod
from pprint import pformat
from typing import Any, ClassVar, Dict, List, Optional

from zuper_commons import ZLogger
from zuper_commons.cmds import ExitCode
from zuper_commons.text import indent
from zuper_commons.types import ZException, ZValueError
from zuper_params import (
    DecentParams,
    DecentParamsResults,
    DecentParamsUserError,
    UserError,
)
from zuper_utils_asyncio import SyncTaskInterface
from zuper_zapp import zapp1, ZappEnv
from . import logger
from .exceptions import QuickAppException

__all__ = [
    "DecentParams",
    "QuickAppBase",
]


class QuickAppBase(ABC):
    """
    class attributes used:

        cmd
        usage
        description (deprecated) => use docstring

    """

    cmd: ClassVar[str] = "unset"
    usage: ClassVar[str] = ""

    # __metaclass__ = ContractsMeta
    options: DecentParamsResults

    def __init__(self, parent=None):
        self.parent = parent
        self._init_logger()

    def _init_logger(self) -> None:
        prog = self.get_prog_name()
        self.logger = ZLogger(prog)

    def info(self, msg: Optional[str] = None, *args: object, **kwargs: object) -> None:
        self.logger.info(msg, *args, stacklevel=1, **kwargs)

    def warn(self, msg: Optional[str] = None, *args: object, **kwargs: object) -> None:
        self.logger.warn(msg, *args, stacklevel=1, **kwargs)

    def error(self, msg: Optional[str] = None, *args: object, **kwargs: object) -> None:
        self.logger.error(msg, *args, stacklevel=1, **kwargs)

    def debug(self, msg: Optional[str] = None, *args: object, **kwargs: object) -> None:
        self.logger.debug(msg, *args, stacklevel=1, **kwargs)

    def __getstate__(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        del d["logger"]
        return d

    def __setstate__(self, d: Any) -> None:
        self.__dict__.update(d)
        self._init_logger()

    @abstractmethod
    def define_program_options(self, params: DecentParams) -> None:
        """Must be implemented by the subclass."""

    @abstractmethod
    async def go2(self, sti: SyncTaskInterface) -> ExitCode:
        """
        Must be implemented. This should return either None to mean success,
        or an integer error code.
        """

    @classmethod
    def get_sys_main(cls):
        """Returns a function to be used as main function for a script."""

        @zapp1()
        async def entry(ze: ZappEnv) -> ExitCode:
            sti = ze.sti
            logger = sti.logger

            logger.info("starting application")
            await sti.started_and_yield()
            args = ze.args
            instance = cls()
            return await instance.main(sti=sti, args=args)

        return entry

    @classmethod
    def __call__(cls, *args: object, **kwargs: object) -> Any:
        main = cls.get_sys_main()
        return main(*args, **kwargs)

    @classmethod
    def get_program_description(cls) -> str:
        """
        Returns a description for the program. This is by default
        looked in the docstring or in the "description" attribute
        (deprecated).
        """
        if cls.__doc__ is not None:
            # use docstring
            docs = cls.__doc__
        else:
            docs = cls.__dict__.get("description", None)

        if docs is None:
            logger.warn("No description at all for %s" % cls)
        else:
            docs = docs.strip()
        return docs

    @classmethod
    def get_short_description(cls) -> Optional[str]:
        longdesc = cls.get_program_description()
        if longdesc is None:
            return None
        return longdesc.strip()  # Todo: extract first sentence

    @classmethod
    def get_usage(cls) -> str:
        """
        Returns an usage string for the program. The pattern ``%prog``
        will be substituted with the name of the program.
        """
        usage = cls.__dict__.get("usage", None)
        if usage is None:
            pass
        else:
            usage = usage.strip()
        return usage

    @classmethod
    def get_epilog(cls) -> Optional[str]:
        """
        Returns the string used as an epilog in the help text.
        """
        return None

    @classmethod
    def get_prog_name(cls) -> str:
        """
        Returns the string used as the program name. By default
        it is contained in the ``cmd`` attribute.
        """
        if not "cmd" in cls.__dict__:
            return os.path.basename(sys.argv[0])
        else:
            return cls.__dict__["cmd"]

    def get_options(self) -> DecentParamsResults:
        return self.options

    def set_parent(self, parent: "QuickAppBase") -> None:
        self.parent = parent

    def get_parent(self) -> Optional["QuickAppBase"]:
        if self.parent is not None:
            assert self.parent != self
        return self.parent

    async def main(
        self,
        sti: SyncTaskInterface,
        args: Optional[List[str]] = None,
        parent: "Optional[QuickAppBase]" = None,
    ) -> ExitCode:
        """Main entry point. Returns an integer as an error code."""
        sti.logger.info(f"{type(self).__name__}.main", args=args, parent=parent)
        # sys.stderr.write(f'HERE! ars = {args} \n')

        if "short" in type(self).__dict__:
            msg = f'Class {type(self)} uses deprecated attribute "short".'
            msg += ' Use "description" instead.'
            self.error(msg)

        # Create the parameters and set them using args
        self.parent = parent

        try:
            self.set_options_from_args(args)
        except DecentParamsUserError as e:
            self.logger.user_error(str(e))
            sys.stderr.write(str(e) + "\n")
            return ExitCode.WRONG_ARGUMENTS

        profile = os.environ.get("QUICKAPP_PROFILE", False)

        if not profile:
            ret = await self.go2(sti)
        else:
            ret = None
            import cProfile

            out = profile
            print("writing to %r" % out)
            cProfile.runctx("self.go()", globals(), locals(), out)
            import pstats

            p = pstats.Stats(out)
            n = 30
            p.sort_stats("cumulative").print_stats(n)
            p.sort_stats("time").print_stats(n)

        if ret is None:
            ret = ExitCode.OK

        if isinstance(ret, int):
            return ret
        else:
            msg = f"Expected None or an integer fomr self.go(), got {ret}"
            raise ValueError(msg)

    def set_options_from_dict(self, config: Dict[str, Any]) -> None:
        """
        Reads the configuration from a dictionary.

        raises: UserError: Wrong configuration, user's mistake.
                Exception: all other exceptions
        """
        params = DecentParams()
        self.define_program_options(params)

        try:
            self.options = params.get_dpr_from_dict(config)
        except DecentParamsUserError as e:
            raise QuickAppException(str(e))
        except Exception as e:
            msg = "Could not interpret:\n"
            msg += indent(pformat(config), "| ")
            msg += "according to params spec:\n"
            msg += indent(str(params), "| ") + "\n"
            msg += "Error is:\n"
            #             if isinstance(e, DecentParamsUserError):
            #                 msg += indent(str(e), '> ')
            #             else:
            msg += indent(traceback.format_exc(), "> ")
            raise QuickAppException(msg)  # XXX class

    def set_options_from_args(self, args: List[str]) -> None:
        """
        Reads the configuration from command line arguments.

        raises: UserError: Wrong configuration, user's mistake.
                Exception: all other exceptions

        """
        if args is None:
            raise ZValueError("args is None")
        cls = type(self)
        prog = cls.get_prog_name()
        params = DecentParams()
        self.define_program_options(params)
        if not params.params:
            msg = "No params defined"
            raise ZException(msg, prog=prog, cls=cls, f=self.define_program_options)

        try:
            usage = cls.get_usage()
            if usage:
                usage = usage.replace("%prog", prog)

            desc = cls.get_program_description()
            epilog = cls.get_epilog()
            self.options = params.get_dpr_from_args(
                prog=prog, args=args, usage=usage, description=desc, epilog=epilog
            )
        except UserError:
            raise
        except SystemExit:
            raise
        except Exception as e:
            msg = "Could not interpret arguments"
            # msg += " args = %s\n" % args
            # msg += "according to params spec:\n"
            # msg += indent(str(params), "| ") + "\n"
            # msg += "Error is:\n"
            # msg += indent(traceback.format_exc(), "> ")
            raise ZException(
                msg,
                prog=prog,
                cls=cls,
                args=args,
                params=params,
                e=traceback.format_exc(),
            ) from e  # XXX class

    # Implementation

    def _define_options_compmake(self, params: DecentParams) -> None:
        script_name = self.get_prog_name()
        s = script_name
        s = s.replace(".py", "")
        s = s.replace(" ", "_")
        default_output_dir = "out-%s/" % s

        g = "Generic arguments for Quickapp"
        # TODO: use  add_help=False to ARgParsre
        # params.add_flag('help', short='-h', help='Shows help message')
        params.add_flag("contracts", help="[deprecated]", group=g)
        params.add_flag("profile", help="Use Python Profiler", group=g)
        params.add_flag("compress", help="Compress stored data", group=g)
        params.add_string(
            "output",
            short="o",
            help="Output directory",
            default=default_output_dir,
            group=g,
        )
        params.add_string(
            "db",
            help="DB directory",
            default=None,
            group=g,
        )

        params.add_flag("reset", help="Deletes the output directory", group=g)
        # params.add_flag('compmake', help='Activates compmake caching (if app is such that
        # set_default_reset())', group=g)

        params.add_flag("console", help="Use Compmake console", group=g)

        params.add_string(
            "command",
            short="c",
            help="Command to pass to compmake for batch mode",
            default=None,
            group=g,
        )
