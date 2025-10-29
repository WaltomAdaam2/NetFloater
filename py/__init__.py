"""
NetFloater - Network Traffic Monitor
A PyQt5-based desktop network traffic monitoring floating window
"""

__version__ = "1.0.0"
__author__ = "WaltomAdaam2"
__description__ = "Network traffic monitoring floating window"

from .config_manager import ConfigManager
from .network_monitor import NetworkMonitor
from .auto_start_manager import AutoStartManager
from .ui_painter import UIPainter


__all__ = ['ConfigManager', 'NetworkMonitor', 'AutoStartManager', 'UIPainter']
