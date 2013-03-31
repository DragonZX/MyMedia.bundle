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
from optparse import OptionParser
import peoplepage_test


if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option('-x', '--exclude-remote', action='store_true', default=False, dest='excludeRemote',
      help='Excludes tests that attempt to download remote content.')
  (options, args) = parser.parse_args()

  runner = unittest.TextTestRunner()
  result = runner.run(peoplepage_test.suite(options.excludeRemote))
  exitCode = 0
  if len(result.errors) > 0 or len(result.failures) > 0:
    exitCode = 1
  sys.exit(exitCode)
