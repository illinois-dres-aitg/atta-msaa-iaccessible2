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

from win_atta_base import Atta
from win_atta_base import get_cmdline_options

import pyia2
from pyia2.utils import IA2Lib
from pyia2.utils import AccessibleDocument


class IAccessibleAtta(Atta):
    """Accessible Technology Test Adapter to test IAccessible2 support."""

    def __init__(self, host, port, ansi_formatting, name="ATTA for MSAA", version="0.5", api="MSAA"):
        """Initializes this ATTA."""

        super(IAccessibleAtta, self).__init__(host, port, name, version, api, Atta.LOG_INFO)

get_cmdline_options()
# Function moved to win_atta_base

if __name__ == "__main__":
    print("Starting ATTA for MSAA (e.g. IAccessible Interfaces)")
    ia_atta = IAccessibleAtta("localhost", 4119, False)
    if not ia_atta.is_enabled():
        print("not enabled")
        sys.exit(1)
    ia_atta.start(ia_atta)
    pyia2.Registry.start()
