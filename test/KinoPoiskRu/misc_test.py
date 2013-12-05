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

import sys, unittest, translit, common
import pluginsettings as S
import testutil as U, testlog
import pageparser # Expect KinoPoiskRu's code in classpath or in the same directory.


def suite(excludeRemoteTests = False):
  suite = unittest.TestSuite()
  suite.addTest(MiscTest('localTest_parsePosterThumbnailData_None'))
  suite.addTest(MiscTest('localTest_computeTitlePenalty_simple'))
  suite.addTest(MiscTest('localTest_computeTitlePenalty_negative'))
  suite.addTest(MiscTest('localTest_computeTitlePenalty_partial'))
  suite.addTest(MiscTest('localTest_scoreMediaTitleMatch'))
  if not excludeRemoteTests:
    suite.addTest(MiscTest('remoteTest_fetchAndParseSearchResults'))
    suite.addTest(MiscTest('remoteTest_fetchAndParseSearchResults_latin'))
    suite.addTest(MiscTest('remoteTest_fetchAndParseSearchResults_latin2'))
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

  def localTest_computeTitlePenalty_simple(self):
    """ Tests penalty for simple title cases.
    """
    penalty = common.computeTitlePenalty(u'Гладиаторы Рима', u'Гладиаторы Рима')
    self._assertEquals(0, penalty, 'Should be no penalty.')
    penalty = common.computeTitlePenalty(u'гладиаторы рима', u'Гладиаторы Рима')
    self._assertEquals(0, penalty, 'Should be no penalty.')
    penalty = common.computeTitlePenalty(u'ГЛАДИАТОРЫ РИМА', u'Гладиаторы Рима')
    self._assertEquals(0, penalty, 'Should be no penalty.')
    penalty = common.computeTitlePenalty(u'Гладиатору Рима', u'Гладиаторы Рима')
    self._assertEquals(2, penalty, 'Wrong penalty.')
    penalty = common.computeTitlePenalty(u'Гладиатору Рома', u'Гладиаторы Рима')
    self._assertEquals(5, penalty, 'Wrong penalty.')
    penalty = common.computeTitlePenalty(u'Кавказская пленница', u'пленница Кавказская')
    self._assertEquals(18, penalty, 'Wrong penalty.')

  def localTest_computeTitlePenalty_negative(self):
    """ Tests penalty for titles that do NOT represent the same movie.
    """
    penalty = common.computeTitlePenalty(u'Неттакого фильма', u'Кавказская пленница')
    self._assertEquals(34, penalty, 'Wrong penalty.')
    penalty = common.computeTitlePenalty(u'some title', u'Кавказская пленница')
    self._assertEquals(37, penalty, 'Wrong penalty.')
    penalty = common.computeTitlePenalty(u'sometitle', u'Кавказская пленница, или Новые приключения Шурика')
    self._assertEquals(40, penalty, 'Wrong penalty.')

  def localTest_computeTitlePenalty_partial(self):
    """ Tests penalty for partial matches.
    """
    penalty = common.computeTitlePenalty(u'Кавказская пленница', u'Кавказская пленница, или Новые приключения Шурика')
    self._assertEquals(6, penalty, 'Wrong penalty.')
    penalty = common.computeTitlePenalty(u'кавказская', u'Кавказская пленница, или Новые приключения Шурика')
    self._assertEquals(8, penalty, 'Wrong penalty.')
    penalty = common.computeTitlePenalty(u'кавказец', u'Кавказская пленница, или Новые приключения Шурика')
    self._assertEquals(21, penalty, 'Wrong penalty.')

  def localTest_scoreMediaTitleMatch(self):
    score = common.scoreMediaTitleMatch('Gladiatory Rima', '2012', u'Гладиаторы Рима', 'Gladiatori di Roma', '2012', 3)
    self._assertEquals(92, score, 'Wrong score.')
    score = common.scoreMediaTitleMatch(u'Кавказская пленница', '1966', u'Кавказская пленница, или Новые приключения Шурика', None, '1966', 0)
    self._assertEquals(94, score, 'Wrong score.')

  def remoteTest_fetchAndParseSearchResults(self):
    results = self.parser.fetchAndParseSearchResults(u'здравствуйте я ваша тетя', '1975')
    self.assertIsNotNone(results, 'results is None.')
    self._assertEquals(5, len(results), 'Wrong number of search results.')
    self._assertTitleTuple(results[0], '77276', 'Здравствуйте, я ваша тетя! (ТВ)', '1975', 95)
    self._assertTitleTuple(results[1], '18731', 'Здравствуйте, я ваша тетушка', '1998', 77)
    self._assertTitleTuple(results[2], '325776', 'Здравствуйте, мы ваша крыша!', '2005', 69)
    self._assertTitleTuple(results[3], '425067', 'Здравствуйте, я приехал!', '1979', 64)

  def remoteTest_fetchAndParseSearchResults_latin(self):
    results = self.parser.fetchAndParseSearchResults('Gladiatory.Rima', '2012')
    self.assertIsNotNone(results, 'results is None.')
    self._assertEquals(6, len(results), 'Wrong number of search results.')
    self._assertTitleTuple(results[0], '612070', 'Гладиаторы футбола (ТВ)', '2008', 72)
    self._assertTitleTuple(results[1], '470718', 'У ворот Рима', '2004', 59)
    self._assertTitleTuple(results[2], '346217', 'Andoroido gaaru Rima: Shirei onna-gokoro o insutooru seyo! (видео)', '2003', 48)
    self._assertTitleTuple(results[3], '597580', 'Гладиаторы Рима', '2012', 89)

  def remoteTest_fetchAndParseSearchResults_latin2(self):
    results = self.parser.fetchAndParseSearchResults('zdravstvuete ya vasha tetya', '1975')
    self.assertIsNotNone(results, 'results is None.')
    self._assertEquals(6, len(results), 'Wrong number of search results.')
    self._assertTitleTuple(results[0], '77276', 'Здравствуйте, я ваша тетя! (ТВ)', '1975', 94)
    self._assertTitleTuple(results[1], '325776', 'Здравствуйте, мы ваша крыша!', '2005', 69)
    self._assertTitleTuple(results[2], '279775', 'Ваша честь (сериал)', '2006', 53)
    self._assertTitleTuple(results[3], '451394', 'Тётя Клава фон Геттен (ТВ)', '2009', 44)
    self._assertTitleTuple(results[4], '424515', 'Ваша остановка, мадам! (ТВ)', '2009', 46)


######## TESTS END HERE ######################################################

  def _assertTitleTuple(self, tuple, kinopoiskId, title, year, score):
    self._assertEquals(title, tuple[1].encode('utf8'), 'Wrong title')
    self._assertEquals(year, tuple[2], 'Wrong year')
    self._assertEquals(kinopoiskId, tuple[0], 'Wrong kinopoisk id')
    self._assertEquals(score, tuple[3], 'Wrong score')


if __name__ == '__main__':
  # When changing this code, pls make sure to adjust main.py accordingly.
  (options, args) = U.parseTestOptions()
  testlog.logLevel = options.logLevel
  runner = unittest.TextTestRunner(verbosity=testlog.TEST_RUNNER_VERBOSITY)
  result = runner.run(suite(options.excludeRemote))
  sys.exit(U.getExitCode(result))

