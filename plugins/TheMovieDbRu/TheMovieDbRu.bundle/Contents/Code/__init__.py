# -*- coding: utf-8 -*-
#
# Russian metadata plugin for Plex, which uses http://api.themoviedb.org/ to get the tag data.
# Copyright (C) 2012 Zhenya Nyden
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
# @version @PLUGIN.REVISION@
# @revision @REPOSITORY.REVISION@

import time
import tmdb, common

IS_DEBUG = False # TODO - DON'T FORGET TO SET IT TO FALSE FOR A DISTRO.

# Default plugin preferences. When modifying, please also change
# corresponding values in the ../DefaultPrefs.json file.
TMDBRU_PREF_DEFAULT_CACHE_TIME = CACHE_1MONTH

# Plugin preferences.
PREFS = common.Preferences(
  (None, None), # imageChoiceName
  (None, None), # maxPostersName
  (None, None), # maxArtName
  (None, None), # getAllActorsName
  ('tmdbru_pref_cache_time', TMDBRU_PREF_DEFAULT_CACHE_TIME))


def Start():
  Log.Info('***** START ***** %s' % common.USER_AGENT)
  PREFS.readPluginPreferences()


def ValidatePrefs():
  Log.Info('***** updating preferences...')
  PREFS.readPluginPreferences()


class TheMovieDbRuAgent(Agent.Movies):
  name = 'TheMovieDbRu'
  languages = [Locale.Language.Russian]
  primary_provider = True
  fallback_agent = False
  accepts_from = None
  contributes_to = None

  def search(self, results, media, lang):
    Log.Debug('SEARCH START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    mediaName = media.name
    mediaYear = media.year
    Log.Debug('searching for name="%s", year="%s", guid="%s", hash="%s", primary_metadata="%s", openSubtitlesHash="%s"...' %
        (str(mediaName), str(mediaYear), str(media.guid), str(media.hash), str(media.primary_metadata), str(media.openSubtitlesHash)))
    tmdb.searchForImdbTitles(results, mediaName, mediaYear, lang)

    if IS_DEBUG:
      common.printSearchResults(results)
    Log.Debug('SEARCH END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

  def update(self, metadata, media, lang):
    Log.Debug('UPDATE START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    # TODO(zhenya): implement the update method.
    Log.Debug('UPDATE END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    pass

