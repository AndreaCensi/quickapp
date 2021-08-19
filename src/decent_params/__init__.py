__version__ = "devel"

from zuper_commons import ZLogger

logger = ZLogger(__name__)


from .utils import UserError


class Choice(list):
    pass


from .decent_param import *
from .decent_params_imp import *
from .exceptions import *
