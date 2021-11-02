import argparse
import logging
import sys
import traceback
from argparse import (
    ArgumentError,
    ArgumentParser,
    PARSER,
    RawTextHelpFormatter,
    REMAINDER,
)
from gettext import gettext as _
from pprint import pformat
from typing import Any, Dict, List, Tuple

from decent_params import Choice
from zuper_commons.types import ZValueError
from .decent_param import (
    DecentParam,
    DecentParamChoice,
    DecentParamFlag,
    DecentParamMultiple,
    DecentParamsResults,
)
from .exceptions import (
    DecentParamsDefinitionError,
    DecentParamsUnknownArgs,
    DecentParamsUserError,
)

__all__ = ["DecentParams"]


class DecentParams:
    def __init__(self, usage=None, prog=None):
        self.usage = usage
        self.prog = prog
        self.params = {}
        self.accepts_extra = False
        self.accepts_extra_description = None
        self.subcommands = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "DecentParams(%s;extra=%s)" % (pformat(self.params), self.accepts_extra)

    def _add(self, p):
        if p.name in self.params:
            msg = f"I already know param {p.name!r}."
            raise DecentParamsDefinitionError(msg)
        p.order = len(self.params)
        self.params[p.name] = p

    def accept_extra(self, description=None):
        """Declares that extra arguments are ok."""
        self.accepts_extra = True
        self.accepts_extra_description = description

    def add_flag(self, name, **args):
        if not "default" in args:
            args["default"] = False
        self._add(DecentParamFlag(ptype=bool, name=name, **args))

    def add_string(self, name, **args):
        S = str
        self._add(DecentParam(ptype=S, name=name, **args))

    def add_float(self, name, **args):
        self._add(DecentParam(ptype=float, name=name, **args))

    def add_int(self, name, **args):
        self._add(DecentParam(ptype=int, name=name, **args))

    def add_bool(self, name, **args):
        self._add(DecentParam(ptype=bool, name=name, **args))

    def add_string_list(self, name, **args):
        self._add(DecentParamMultiple(ptype=str, name=name, **args))

    def add_float_list(self, name, **args):
        self._add(DecentParamMultiple(ptype=float, name=name, **args))

    def add_int_list(self, name, **args):
        self._add(DecentParamMultiple(ptype=int, name=name, **args))

    def add_int_choice(self, name, choices, **args):
        self._add(DecentParamChoice(name=name, choices=choices, ptype=int, **args))

    def add_float_choice(self, name, choices, **args):
        self._add(DecentParamChoice(name=name, choices=choices, ptype=float, **args))

    def add_string_choice(self, name, choices, **args):
        self._add(DecentParamChoice(name=name, choices=choices, ptype=str, **args))

    def parse_args(self, args, allow_choice=True):  # TODO @UnusedVariable
        parser = self.create_parser()
        values, given = self.parse_using_parser(parser, args)
        # TODO: check no Choice()
        res = DecentParamsResults(values, given, self.params)
        return res

    def parse_using_parser(self, parser, args: List[str]) -> Tuple[Dict, List[str]]:
        """
        Returns a dictionary with all values of parameters,
        but possibly some values are Choice() instances.

        """
        try:
            argparse_res, argv = parser.parse_known_args(args)
            if argv:
                msg = "Extra arguments found: %s" % argv
                raise DecentParamsUnknownArgs(msg, _=self)
        except SystemExit:
            raise  # XXX
            # raise Exception(e)  # TODO

        values, given = self._interpret_args(argparse_res)
        return values, given

    def parse_using_parser_extra(self, parser, args: List[str]) -> Tuple[Dict, List[str], List[str]]:
        """
        This returns also the extra parameters

        returns: values, given, extra
        """
        if args is None:
            raise ZValueError("args is None")

        try:
            #             if False:
            #                 if self.accepts_extra:
            #                     parser.add_argument('remainder', nargs=argparse.REMAINDER)
            #                 argparse_res, unknown = parser.parse_known_args(args)
            #             else:
            if self.accepts_extra:
                parser.add_argument("remainder", nargs="*", help=self.accepts_extra_description)
            # argparse_res, unknown = parser.parse_known_args(args)
            argparse_res, unknown = parser.parse_known_intermixed_args(args=args)
        #                 print('argparse_res: %s' % argparse_res)
        #                 print('unknown: %s' % unknown)
        except SystemExit as e:
            if e.code == 0 and ("-h" in args or "--help" in args):
                raise
            sys.stderr.write("System exit: " + traceback.format_exc())
            raise  # XXX

        if self.accepts_extra:
            extra = argparse_res.remainder
        else:
            extra = []

        if unknown and not self.subcommands:
            helps = parser.format_help()
            sys.stderr.write("raising arguments")
            raise DecentParamsUnknownArgs(
                all_args=args,
                known=argparse_res,
                extra=extra,
                unknown=unknown,
                _=self,
                helps=helps,
            )

        values, given = self._interpret_args(argparse_res)
        # TODO: raise if extra is given

        #         print('extra: %r' % extra)
        return values, given, extra

    def _interpret_args(self, argparse_res):
        parsed = vars(argparse_res)
        return self._interpret_args2(parsed)

    def _interpret_args2(self, parsed: Dict) -> Tuple[Dict, List[str]]:
        values = dict()
        given = set()
        for k, v in list(self.params.items()):
            # if v.compulsory and parsed[k] is None:
            if v.compulsory and (not k in parsed or parsed[k] is None):
                msg = "Compulsory option %r not given." % k
                raise DecentParamsUserError(msg, _=self)

            # warnings.warn('Not sure below')
            # if parsed[k] is not None:
            if k in parsed and parsed[k] is not None:
                if parsed[k] != self.params[k].default:
                    given.add(k)
                    if isinstance(self.params[k], DecentParamMultiple):
                        if isinstance(parsed[k], list):
                            values[k] = parsed[k]
                        else:
                            values[k] = [parsed[k]]
                    else:
                        if isinstance(parsed[k], list):
                            if len(parsed[k]) > 1:
                                values[k] = Choice(parsed[k])
                            else:
                                values[k] = parsed[k][0]
                        else:
                            values[k] = parsed[k]
                    # values[k] = self.params[k].value_from_string(parsed[k])
                else:
                    values[k] = self.params[k].default
            else:
                values[k] = self.params[k].default
        return values, list(given)

    def _populate_parser(self, option_container, prog=None):
        groups = set(p.group for p in list(self.params.values()))
        for g in groups:

            if g is None:  # normal arguments:
                title = "Arguments for %s" % prog
            else:
                title = str(g)
            description = None
            group = option_container.add_argument_group(title=title, description=description)
            g_params = [p for p in list(self.params.values()) if p.group == g]
            for p in g_params:
                p.populate(group)

    def create_parser(self, prog=None, usage=None, epilog=None, description=None):
        usage0 = usage

        def my_formatter(prog):
            return RawTextHelpFormatter(prog=prog, max_help_position=90, width=None)

        class MyParser(argparse.ArgumentParser):
            def error(self, msg):
                raise DecentParamsUserError(msg, _=self)

            def format_help(self):
                formatter = self._get_formatter()

                def add_dash(s, char):
                    dash = char * len(s)
                    return "\n".join((dash, s, dash))

                s = "Documentation for the command '%s'" % self.prog

                formatter.add_text(add_dash(s, "="))
                # first description
                formatter.add_text(self.description)
                formatter.add_text("\n")

                #                 print('usage0: %r' % usage0)
                #                 print('usage: %r' % self.usage)
                #
                if usage0 is not None:
                    formatter.add_text(add_dash("Usage and examples", "-"))

                    formatter.add_text(usage0)

                formatter.add_text(add_dash("Formal description of arguments", "-"))

                formatter.add_text(self.usage)

                # positionals, optionals and user-defined groups
                for action_group in self._action_groups:
                    formatter.start_section(action_group.title)
                    formatter.add_text(action_group.description)
                    formatter.add_arguments(action_group._group_actions)
                    formatter.end_section()

                # epilog
                formatter.add_text(self.epilog)

                # determine help from format above
                return formatter.format_help()

        # give None here
        # noinspection PyTypeChecker
        parser = MyParser(
            prog=prog,
            usage=None,
            epilog=epilog,
            description=description,
            formatter_class=my_formatter,
        )
        self._populate_parser(option_container=parser, prog=prog)
        return parser

    def get_dpr_from_args(self, args: List[str], prog=None, usage=None, epilog=None, description=None):
        parser = self.create_parser(prog=prog, usage=usage, epilog=epilog, description=description)

        values, given, extra = self.parse_using_parser_extra(parser, args)
        if extra and not self.accepts_extra:
            msg = "Found extra arguments not accepted: %s" % extra
            raise DecentParamsUserError(msg, _=self)
        dpr = DecentParamsResults(values, given, self, extra=extra)
        return dpr

    def get_dpr_from_dict(self, config: Dict[str, Any]):
        args = []
        for k, v in list(config.items()):
            args.append("--%s" % k)
            args.append(v)
        return self.get_dpr_from_args(args)


# from warnings import warn
# logging.basicConfig(format="%(levelname)s: Intermix: %(message)s")


def warn(message):
    logging.warning(message)


def parse_intermixed_args(self, args=None, namespace=None):
    args, argv = self.parse_known_intermixed_args(args, namespace)
    if argv:
        msg = _("unrecognized arguments: %s")
        self.error(msg % " ".join(argv))
    return args


def parse_known_intermixed_args(self, args=None, namespace=None, _fallback=None):
    # self - argparse parser
    # args, namespace - as used by parse_known_args
    # _fallback - action to take if it can't handle this parser's arguments
    #      (default raises an error)
    # returns a namespace and list of extras

    # positional can be freely intermixed with optionals
    # optionals are first parsed with all positional arguments deactivated
    # the 'extras' are then parsed
    # positionals 'deactivated' by setting nargs=0

    positionals = self._get_positional_actions()

    a = [action for action in positionals if action.nargs in [PARSER, REMAINDER]]
    if a:
        if _fallback is None:
            a = a[0]
            err = ArgumentError(a, "parse_intermixed_args: positional arg with nargs=%s" % a.nargs)
            self.error(str(err))
        else:
            return _fallback(args, namespace)

    if [
        action.dest
        for group in self._mutually_exclusive_groups
        for action in group._group_actions
        if action in positionals
    ]:
        if _fallback is None:
            self.error("parse_intermixed_args: positional in mutuallyExclusiveGroup")
        else:
            return _fallback(args, namespace)

    save_usage = self.usage
    try:
        if self.usage is None:
            # capture the full usage for use in error messages
            self.usage = self.format_usage()[7:]
        for action in positionals:
            # deactivate positionals
            action.save_nargs = action.nargs
            action.nargs = 0
        try:
            namespace, remaining_args = self.parse_known_args(args, namespace)
            for action in positionals:
                # remove the empty positional values from namespace
                if hasattr(namespace, action.dest):
                    delattr(namespace, action.dest)
        except SystemExit:
            # warn('error from 1st parse_known_args')
            raise
        finally:
            # restore nargs and usage before exiting
            for action in positionals:
                action.nargs = action.save_nargs
            # self.usage = save_usage
        # logging.info('1st: %s,%s'%(namespace, remaining_args))
        # parse positionals
        # optionals aren't normally required, but just in case, turn that off
        optionals = self._get_optional_actions()
        for action in optionals:
            action.save_required = action.required
            action.required = False
        for group in self._mutually_exclusive_groups:
            group.save_required = group.required
            group.required = False
        try:
            namespace, extras = self.parse_known_args(remaining_args, namespace)
        except SystemExit:
            warn("error from 2nd parse_known_args")
            raise
        finally:
            # restore parser values before exiting
            for action in optionals:
                action.required = action.save_required
            for group in self._mutually_exclusive_groups:
                group.required = group.save_required
    finally:
        self.usage = save_usage
    return namespace, extras


ArgumentParser.parse_intermixed_args = parse_intermixed_args
ArgumentParser.parse_known_intermixed_args = parse_known_intermixed_args
