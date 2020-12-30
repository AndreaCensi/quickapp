from zuper_commons.types import ZException
from .utils import UserError

__all__ = [
    "DecentParamsUserError",
    "DecentParamsUnknownArgs",
    "DecentParamsSemanticError",
]


class DecentParamsDefinitionError(ZException):
    """ These are raised when constructing data structures """

    pass


class DecentParamsUserError(UserError):
    """ These are raised when interrpreting arguments """

    #
    # def __init__(self, dp, msg):
    #     self.dp = dp
    #     self.msg = msg
    #     s = msg
    #     #         s += '\n' + str(dp)
    #     Exception.__init__(self, s)


class DecentParamsSemanticError(DecentParamsUserError):
    pass
    # def __init__(self, dp, p, msg):
    #     self.p = p
    #     s = msg + "\n while interpreting parameter %s " % p
    #     DecentParamsUserError.__init__(self, dp, s)


class DecentParamsUnknownArgs(DecentParamsUserError):
    pass
    # def __init__(self, dp, unknown):
    # msg = "Could not interpret %r." % unknown
    # msg += "\n" + "Known parameters: %s." % ", ".join(dp.params)
    # DecentParamsUserError.__init__(self, dp, msg)
