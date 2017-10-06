#!/usr/bin/env python27
#
# ia2_atta
#
# Accessible Technology Test Adapter for MSAA+IAccessible2
# Tests MSAA+IAccessible2 (server-side) implementations via MSAA+IAccessible2 (client-side)
#
# Developed by Jon Gunderson, Bei Zhang and Naijing Zhang
# Copyright (c) 2017 University of Illinois
# Based on the ATTAs developed by Joanmarie Diggs (@joanmarie)
#
# For license information, see:
# https://www.w3.org/Consortium/Legal/2008/04-testsuite-copyright.html

# import argparse
import re
import sys
import threading
import signal

from win_atta_base import Atta
from win_atta_base import get_cmdline_options

import pyia2
from pyia2.utils import IA2Lib
from pyia2.utils import AccessibleDocument


class IAccessible2Atta(Atta):
    """Accessible Technology Test Adapter to test IAccessible2 support."""

    def __init__(self, host, port, ansi_formatting, name="ATTA for IA2", version="0.5", api="IAccessible2"):
        """Initializes this ATTA."""

        super(IAccessible2Atta, self).__init__(host, port, name, version, api, Atta.LOG_INFO)

get_cmdline_options()
# Function moved to win_atta_base

if __name__ == "__main__":
    print("Starting ATTA for IAccessible2 Interfaces")
    ia2_atta = IAccessible2Atta("localhost", 4119, False)
    if not ia2_atta.is_enabled():
        print("ia2_atta is not enabled.")
        sys.exit(1)
    ia2_atta.start(ia2_atta)
    pyia2.Registry.start()
    print("Shutting down...")
    ia2_atta.shutdown(ia2_atta, signal.SIGTERM)
    sys.exit(1)
