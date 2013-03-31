# -*- coding: utf-8 -*-
#
# Main test suite for the KinoPoiskRu Plex metadata plugin.
#
# Copyright (C) 2012  Zhenya Nyden
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# @author zhenya (Yevgeny Nyden)
#

import unittest, sys
import testutil as U, peoplepage_test


if __name__ == '__main__':
  # When changing this code, pls make sure to adjust __main__ method
  # in individual test files accordingly (in case we'd want to run them separately).
  (options, args) = U.parseTestOptions()
  peoplepage_test.logLevel = options.logLevel
  runner = unittest.TextTestRunner(verbosity=2)
  result = runner.run(peoplepage_test.suite(options.excludeRemote))
  sys.exit(U.getExitCode(result))
