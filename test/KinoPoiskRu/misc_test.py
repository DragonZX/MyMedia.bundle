# -*- coding: utf-8 -*-
#
# Title page tests.
# @author zhenya (Yevgeny Nyden)
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

import sys, unittest, translit
import pluginsettings as S
import testutil as U, testlog
import pageparser # Expect KinoPoiskRu's code in classpath or in the same directory.


def suite(excludeRemoteTests = False):
  suite = unittest.TestSuite()
  suite.addTest(MiscTest('localTest_parsePosterThumbnailData_None'))
#  if not excludeRemoteTests:
#    suite.addTest(ImagePagesTest('remoteTest_someTest'))
  return suite


class MiscTest(U.PageTest):
  def __init__(self, testName):
    super(MiscTest, self).__init__(testName, S.ENCODING_KINOPOISK_PAGE, pageparser.USER_AGENT)

  def setUp(self):
    self.parser = pageparser.PageParser(self.log, self.http, testlog.logLevel > 4)
    if testlog.logLevel > 0:
      sys.stdout.flush()
      print '' # Put log statement on a new line.

  def tearDown(self):
    pass

  ######## TESTS START HERE ####################################################

  def localTest_parsePosterThumbnailData_None(self):
    """ Tests a typical poster page loaded from filesystem. """
    latinStr = 'Operatsiya Y i drugiye priklyucheniya Shurika'
    self._assertEquals('Операция Ы и другиyе приключения Шурика',
        translit.detranslify(latinStr).encode('utf8'), 'Wrong translitirated string')
    latinStr = 'D\'Artanyan i tri mushketyora[kinokopilka].torrent'
    self._assertEquals('Д‘Артанян и три мушкетёра[кинокопилка].торрент',
        translit.detranslify(latinStr).encode('utf8'), 'Wrong translitirated string')



  ######## TESTS END HERE ######################################################



if __name__ == '__main__':
  # When changing this code, pls make sure to adjust main.py accordingly.
  (options, args) = U.parseTestOptions()
  testlog.logLevel = options.logLevel
  runner = unittest.TextTestRunner(verbosity=testlog.TEST_RUNNER_VERBOSITY)
  result = runner.run(suite(options.excludeRemote))
  sys.exit(U.getExitCode(result))

