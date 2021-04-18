__version__ = "1.1"

import sys
import traceback

from zuper_commons.types import ZException


class UserError(ZException):
    pass


def wrap_script_entry_point(function, logger, exceptions_no_traceback=(UserError,), args=None, sys_exit=True):
    """
    Wraps the main() of a script.
    For Exception: we exit with value 2.

    :param exceptions_no_traceback: list of exceptions for which we
     just print the error, and return 1.

    """

    # logger.info('wrap_script_entry_point')

    ret = wrap_script_entry_point_noexit(function, logger, exceptions_no_traceback, args)

    # logger.info('wrap_script_entry_point ret %s' % ret)

    if sys_exit:
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(ret)
    else:
        return ret


def wrap_script_entry_point_noexit(function, logger, exceptions_no_traceback=(UserError,), args=None):
    """
    Wraps the main() of a script.

    :param exceptions_no_traceback: list of exceptions for which we
     just print the error, and return 1.

    """
    if args is None:
        args = sys.argv[1:]
    try:
        ret = function(args)
        if ret is None:
            ret = 0
        return ret
    except exceptions_no_traceback as e:
        # print('no traceback')
        logger.error(e)
        return 1
    except Exception as e:
        # print('normal exception')
        s = traceback.format_exc()
        logger.error(s)
        #         sys.stderr.write(s)
        #         sys.stderr.write('\n')
        #         sys.stderr.flush()
        return 2
