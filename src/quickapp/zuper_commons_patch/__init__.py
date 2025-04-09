#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch module providing implementations for missing functions from zuper_commons.
"""

import re
import logging

# ZLogger implementation
class ZLogger:
    """
    Minimal implementation of ZLogger that wraps standard Python logging.
    This is used as a fallback when the original ZLogger is not available.
    """
    
    def __init__(self, name):
        """Initialize with a logger name."""
        self.logger = logging.getLogger(name)
    
    def debug(self, msg, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """Log an info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """Log an error message."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """Log an exception."""
        self.logger.exception(msg, *args, exc_info=exc_info, **kwargs)

# Natural sorting implementation
def natsorted(seq):
    """
    Sort the given sequence in the way that humans expect.
    This is a reimplementation of natsorted from zuper_commons.text.
    """
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    
    def alphanum_key(key):
        return [convert(c) for c in re.split('([0-9]+)', str(key))]
    
    return sorted(seq, key=alphanum_key)

# Duration formatting implementation
def duration_compact(seconds):
    """
    Format a duration in seconds as a compact string.
    This is a reimplementation of duration_compact from zuper_commons.ui.
    """
    if seconds < 1e-6:
        return "%.1f ns" % (seconds * 1e9)
    elif seconds < 1e-3:
        return "%.1f μs" % (seconds * 1e6)
    elif seconds < 1:
        return "%.1f ms" % (seconds * 1e3)
    elif seconds < 60:
        return "%.1f s" % seconds
    elif seconds < 3600:
        m = int(seconds / 60)
        s = seconds - m * 60
        return "%d m %.1f s" % (m, s)
    else:
        h = int(seconds / 3600)
        seconds = seconds - h * 3600
        m = int(seconds / 60)
        s = seconds - m * 60
        return "%d h %d m %.1f s" % (h, m, s)