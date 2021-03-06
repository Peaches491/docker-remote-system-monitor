#!/usr/bin/env python

from __future__ import print_function
from fabric.api import run
from fabric.api import settings

import re
import sys

class Drive(object):
    def __init__(self, path, timeout=60):
        self.path = path
        self.timeout = timeout
        self._memo_smart = {}

    def _memoize_smart(self):
        with settings(warn_only=True):
            smart = run("smartctl -a " + self.path)
            self._memo_smart = str(smart)
            return smart.succeeded

    def _update(self, force_update=False):
        print("Updating SMART info")
        self._memoize_smart()

    def temperature(self, force_update=False):
        self._update(force_update)
        if not self._memo_smart:
            return None
        # Example temperature line:
        # 194 Temperature_Celsius     0x0002   130   130   000    Old_age   Always       -       46 (Min/Max 24/59)
        match = re.findall("^[0-9]+ Temperature_Celsius.*", self._memo_smart, re.MULTILINE)
        if match:
            return float(match[0].split()[9])



