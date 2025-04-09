__version__ = "6.0.2"

try:
    from zuper_commons.logs import ZLogger
except ImportError:
    # Use our patched version when ZLogger is not available
    from .zuper_commons_patch import ZLogger
    import warnings
    warnings.warn("Using patched ZLogger implementation. Original zuper_commons.logs.ZLogger not found.")

logger = ZLogger(__name__)

# error in computation
QUICKAPP_COMPUTATION_ERROR = 2

# error in passing parameters
QUICKAPP_USER_ERROR = 1

from .utils import col_logging

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
