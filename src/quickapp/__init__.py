__version__ = "7.1.2108111329"
__date__ = "2021-08-11T13:29:26.948205+00:00"

from zuper_commons.logs import ZLogger

logger = ZLogger(__name__)
logger.hello_module(name=__name__, filename=__file__, version=__version__, date=__date__)

# error in computation
QUICKAPP_COMPUTATION_ERROR = 2

# error in passing parameters
QUICKAPP_USER_ERROR = 1

from .quick_app_base import *
from .quick_multi_app import *
from .resource_manager import *
from .report_manager import *
from .quick_app import *
from .compmake_context import *
from .app_utils import *

symbols = [QuickMultiCmdApp, QuickApp, QuickAppBase, add_subcommand, ResourceManager]

for s in symbols:
    s.__module__ = "quickapp"
