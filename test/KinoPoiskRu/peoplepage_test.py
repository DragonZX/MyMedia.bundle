# -*- coding: utf-8 -*-
#
# People page tests.
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

import sys, urllib2, codecs, unittest
from lxml import etree
import pluginsettings as S
import testutil as U
from testlog import TestLogger as Logger

logLevel = 0

# Expect KinoPoiskRu's code in classpath or in the same directory.
import common, pageparser

# A typical page full of actor records: "Остров проклятых" (2009) [eng: "Shutter Island"].
ACTORS_PAGE_397667 = 'data/actors_397667.html'
ACTORS_PAGE_397667_URL = S.KINOPOISK_PEOPLE % '397667' # http://www.kinopoisk.ru/film/397667/cast/

def dump(obj):
  for attr in dir(obj):
    print "obj.%s = %s" % (attr, getattr(obj, attr))


def suite(excludeRemoteTests = False):
  suite = unittest.TestSuite()
  suite.addTest(PeoplePageTest('localTest_peoplePage_notAll'))
  suite.addTest(PeoplePageTest('localTest_peoplePage_all'))
  if not excludeRemoteTests:
    suite.addTest(PeoplePageTest('remoteTest_peoplePage_all'))
  return suite


class PeoplePageTest(unittest.TestCase):
  def setUp(self):
    self.parser = pageparser.PeopleParser(Logger(logLevel), logLevel > 4)
    if logLevel > 0:
      sys.stdout.flush()
      print '' # Put log statement on a new line.

  def tearDown(self):
    pass

  ######## TESTS START HERE ####################################################

  def localTest_peoplePage_notAll(self):
    data = self._readAndParseLocalFile(ACTORS_PAGE_397667, False)
    actors = self._assertActorsDataFound(data, pageparser.MAX_ACTORS)
    self._assertActorsFromPage397667(actors)

  def localTest_peoplePage_all(self):
    data = self._readAndParseLocalFile(ACTORS_PAGE_397667, True)
    actors = self._assertActorsDataFound(data, pageparser.MAX_ALL_ACTORS)
    self._assertActorsFromPage397667(actors)
    self._assertMoreActorsFromPage397667(actors)

  def remoteTest_peoplePage_all(self):
    data = self._requestAndParseHtmlPage(ACTORS_PAGE_397667_URL, True)
    actors = self._assertActorsDataFound(data, pageparser.MAX_ALL_ACTORS)
    self._assertActorsFromPage397667(actors)
    self._assertMoreActorsFromPage397667(actors)

  ######## TESTS END HERE ######################################################

  def _readAndParseLocalFile(self, filename, loadAllActors):
    fileHandle = codecs.open(filename, "r", S.ENCODING_KINOPOISK_PAGE)
    fileContent = fileHandle.read()
    page = etree.HTML(fileContent)
    return self.parser.parse(page, loadAllActors)

  def _requestAndParseHtmlPage(self, url, loadAllActors):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', common.USER_AGENT)]
    response = opener.open(url)
    content = response.read().decode(S.ENCODING_KINOPOISK_PAGE)
    page = etree.HTML(content)
    return self.parser.parse(page, loadAllActors)

  def _assertActorsDataFound(self, data, numberOfActors):
    self.assertIn('actors', data, 'Actors data is not found.')
    actors = data['actors']
    self.assertIsNotNone(actors, 'Actors data is not set.')
    self.assertEquals(numberOfActors, len(actors), 'Wrong number of actors.')
    return actors

  def _assertActorsFromPage397667(self, actors):
    # Just 7 should be enough.
    self._assertActor(actors, 0, 'Леонардо ДиКаприо', 'Teddy Daniels')
    self._assertActor(actors, 1, 'Марк Руффало', 'Chuck Aule')
    self._assertActor(actors, 2, 'Бен Кингсли', 'Dr. Cawley')
    self._assertActor(actors, 3, 'Макс фон Сюдов', 'Dr. Naehring')
    self._assertActor(actors, 4, 'Мишель Уильямс', 'Dolores')
    self._assertActor(actors, 5, 'Эмили Мортимер', 'Rachel 1')
    self._assertActor(actors, 6, 'Патришия Кларксон', 'Rachel 2')

  def _assertMoreActorsFromPage397667(self, actors):
    # A few more actors.
    self._assertActor(actors, 10, 'Элиас Котеас', 'Laeddis')
    self._assertActor(actors, 11, 'Робин Бартлетт', 'Bridget Kearns')
    self._assertActor(actors, 12, 'Кристофер Денхам', 'Peter Breene')
    self._assertActor(actors, 40, 'Джеффри Кораццини', 'Boardroom Guard') # Should have no ', в титрах не указана'.

  def _assertActor(self, actors, index, name, role):
    self.assertGreater(len(actors), index, 'Index too large.')
    actorTuple = actors[index]
    self.assertIsNotNone(actorTuple, 'Actor ' + str(index) + ' tuple is None.')
    self.assertEquals(2, len(actorTuple), 'Wrong number of items in actor ' + str(index) + ' tuple.')
    self._assertStringsEqual(name, actorTuple[0], 'Wrong actor ' + str(index) + ' name.')
    self._assertStringsEqual(role, actorTuple[1], 'Wrong actor ' + str(index) + ' role.')

  def _assertStringsEqual(self, expected, fact, msg):
    self.assertTrue(expected == fact, msg + ' Expected "' + expected + '", but was "' + str(fact) + '".')

if __name__ == '__main__':
  # When changing this code, pls make sure to adjust main.py accordingly.
  (options, args) = U.parseTestOptions()
  logLevel = options.logLevel
  runner = unittest.TextTestRunner(verbosity=2)
  result = runner.run(suite())
  sys.exit(U.getExitCode(result))

