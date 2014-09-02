__version__ = "1.1dev1"

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# error in computation
QUICKAPP_COMPUTATION_ERROR = 2

# error in passing parameters
QUICKAPP_USER_ERROR = 1

from .utils import col_logging
from decent_params import UserError

from .quick_app_base import *
from .quick_multi_app import *
from .resource_manager import *
from .report_manager import *
from .quick_app import *
from .compmake_context import *
from .app_utils import *

symbols = [QuickMultiCmdApp, QuickApp, 
           QuickAppBase, add_subcommand, ResourceManager]

for s in symbols: 
    s.__module__ = 'quickapp'
