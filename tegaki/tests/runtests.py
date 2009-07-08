#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2008 The Tegaki project contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Contributors to this file:
# - Mathieu Blondel

import glob
import os
import sys
import unittest

currdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.join(currdir, "..")

os.chdir(currdir)
sys.path = sys.path + [parentdir]                   

def gettestnames():
    return [name[:-3] for name in glob.glob('test_*.py')]

suite = unittest.TestSuite()
loader = unittest.TestLoader()

for name in gettestnames():
    suite.addTest(loader.loadTestsFromName(name))

testRunner = unittest.TextTestRunner(verbosity=1)
testRunner.run(suite)
