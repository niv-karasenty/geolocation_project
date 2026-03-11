#
# Copyright 2008,2009 Free Software Foundation, Inc.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# The presence of this file turns this directory into a Python package

'''
This is the GNU Radio AOA_MOD module. Place your Python package
description here (python/__init__.py).
'''
import os

# import pybind11 generated symbols into the AoA_mod namespace
try:
    # this might fail if the module is python-only
    from .AoA_mod_python import *
except ModuleNotFoundError:
    pass

# import any pure python here
from .phase_to_angle import phase_to_angle
from .send_to_server import send_to_server

#
