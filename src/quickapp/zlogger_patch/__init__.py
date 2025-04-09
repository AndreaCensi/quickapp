#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch module providing a minimal ZLogger implementation for Python 3 compatibility.
This replaces the missing ZLogger class from zuper_commons.logs.
"""

import logging
import inspect
import os
import traceback

class ZLogger:
    """
    Minimal implementation of ZLogger that wraps standard Python logging.
    This is used as a fallback when the original ZLogger is not available.
    """
    
    def __init__(self, name):
        """Initialize with a logger name."""
        self.logger = logging.getLogger(name)
    
    def _get_caller_info(self):
        """Get information about the caller function."""
        try:
            # Get the frame of the caller's caller
            frame = inspect.currentframe().f_back.f_back
            filename = os.path.basename(frame.f_code.co_filename)
            lineno = frame.f_lineno
            func_name = frame.f_code.co_name
            return f"{filename}:{lineno} - {func_name}"
        except Exception:
            return "unknown:0"
    
    def debug(self, msg, *args, **kwargs):
        """Log a debug message."""
        caller = self._get_caller_info()
        self.logger.debug(f"{caller} | {msg}", *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """Log an info message."""
        caller = self._get_caller_info()
        self.logger.info(f"{caller} | {msg}", *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """Log a warning message."""
        caller = self._get_caller_info()
        self.logger.warning(f"{caller} | {msg}", *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """Log an error message."""
        caller = self._get_caller_info()
        self.logger.error(f"{caller} | {msg}", *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """Log a critical message."""
        caller = self._get_caller_info()
        self.logger.critical(f"{caller} | {msg}", *args, **kwargs)
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """Log an exception."""
        caller = self._get_caller_info()
        self.logger.exception(f"{caller} | {msg}", *args, exc_info=exc_info, **kwargs)