#!/usr/bin/env python

from __future__ import print_function
from fabric.api import run

import re
import sys

class Drive(object):
    def __init__(self, path, timeout=60):
        self.path = path
        self.timeout = timeout
        self._memo_smart = {}

    def _memoize_smart(self):
        smart = run("smartctl -a " + self.path)
        if smart.succeeded:
            self._memo_smart = str(smart)
        else:
            print("drive(%s): could not update smart data!", file=sys.stderr)
            print(smart, file=sys.stderr)
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



