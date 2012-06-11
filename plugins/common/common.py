# -*- coding: utf-8 -*-

# Russian metadata plugin for Plex, which uses http://www.kinopoisk.ru/ to get the tag data.
# Плагин для обновления информации о фильмах использующий КиноПоиск (http://www.kinopoisk.ru/).
# Copyright (C) 2012 Zhenya Nyden

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import string, sys, time

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/534.51.22 (KHTML, like Gecko) Version/5.1.1 Safari/534.51.22'
ENCODING_PLEX = 'utf-8'

PREF_CACHE_TIME_DEFAULT = CACHE_1MONTH

SCORE_PENALTY_ITEM_ORDER = 1
SCORE_PENALTY_YEAR_WRONG = 4
SCORE_PENALTY_NO_MATCH = 50

IMAGE_SCORE_MAX_NUMBER_OF_ITEMS = 5
IMAGE_SCORE_ITEM_ORDER_BONUS_MAX = 30
IMAGE_SCORE_RESOLUTION_BONUS_MAX = 20
IMAGE_SCORE_RATIO_BONUS_MAX = 40
IMAGE_SCORE_THUMB_BONUS = 10
POSTER_SCORE_MIN_RESOLUTION_PX = 60 * 1000
POSTER_SCORE_MAX_RESOLUTION_PX = 600 * 1000
POSTER_SCORE_BEST_RATIO = 0.7
ART_SCORE_BEST_RATIO = 1.5
ART_SCORE_MIN_RESOLUTION_PX = 200 * 1000
ART_SCORE_MAX_RESOLUTION_PX = 1000 * 1000


class Thumbnail:
  """ Represents an image search result data.
  """
  def __init__(self, thumbImgUrl, fullImgUrl, fullImgWidth, fullImgHeight, index, score):
    self.thumbImgUrl = thumbImgUrl
    self.fullImgUrl = fullImgUrl
    self.fullImgWidth = fullImgWidth
    self.fullImgHeight = fullImgHeight
    self.index = index
    self.score = score


class Preferences:
  """ These instance variables are populated from plugin preferences.
  """
  def __init__(self,
      (cacheTimeName, cacheTime),
      (maxPostersName, maxPosters),
      (maxArtName, maxArt),
      (getAllActorsName, getAllActors)):
    self.cacheTimeName = cacheTimeName
    self.cacheTime = cacheTime
    self.maxPostersName = maxPostersName
    self.maxPosters = maxPosters
    self.maxArtName = maxArtName
    self.maxArt = maxArt
    self.getAllActorsName = getAllActorsName
    self.getAllActors = getAllActors

  def readPluginPreferences(self):
    # Setting cache expiration time.
    prefCache = Prefs[self.cacheTimeName]
    if prefCache == u'1 минута':
      self.cacheTime = CACHE_1MINUTE
    elif prefCache == u'1 час':
      self.cacheTime = CACHE_1HOUR
    elif prefCache == u'1 день':
      self.cacheTime = CACHE_1DAY
    elif prefCache == u'1 неделя':
      self.cacheTime = CACHE_1DAY
    elif prefCache == u'1 месяц':
      self.cacheTime = CACHE_1MONTH
    elif prefCache == u'1 год':
      self.cacheTime = CACHE_1MONTH * 12
    else:
      self.cacheTime = PREF_CACHE_TIME_DEFAULT
    HTTP.CacheTime = self.cacheTime
    Log.Debug('PREF: Setting cache expiration to %d seconds (%s).' % (self.cacheTime, prefCache))

    self.maxPosters = int(Prefs[self.maxPostersName])
    Log.Debug('PREF: Max poster results is set to %d.' % self.maxPosters)
    self.maxArt = int(Prefs[self.maxArtName])
    Log.Debug('PREF: Max art results is set to %d.' % self.maxArt)
    self.getAllActors = Prefs[self.getAllActorsName]
    Log.Debug('PREF: Parse all actors is set to %s.' % str(self.getAllActors))


def getElementFromHttpRequest(url, encoding):
  """ Fetches a given URL and returns it as an element.
      Функция преобразования html-кода в xml-код.
  """
#  Log.Debug('Requesting URL: "%s"...' % url)
  for i in range(3):
    try:
#      time.sleep(1)
      response = HTTP.Request(url, headers = {'User-agent': USER_AGENT, 'Accept': 'text/html'})
      return HTML.ElementFromString(str(response).decode(encoding))
    except:
      Log.Debug('Error fetching URL: "%s".' % url)
      time.sleep(1)
  return None


def printSearchResults(results):
  """ Sends a list of media results to debug log.
  """
  Log.Debug('Search produced %d results:' % len(results))
  index = 0
  for result in results:
    Log.Debug(' ... %d: id="%s", name="%s", year="%s", score="%d".' %
              (index, result.id, result.name, str(result.year), result.score))
    index += 1


def printImageSearchResults(thumbnailList):
  Log.Debug('image search produced %d results:' % len(thumbnailList))
  index = 0
  for result in thumbnailList:
    Log.Debug(' ... result %d: index="%s", score="%s", URL="%s".' %
              (index, result.index, result.score, result.fullImgUrl))
    index += 1
  return None


def logException(msg):
  excInfo = sys.exc_info()
  Log.Exception('%s; exception: %s; cause: %s' % (msg, excInfo[0], excInfo[1]))


def scoreMediaTitleMatch(mediaName, mediaYear, title, year, itemIndex):
  """ Compares page and media titles taking into consideration
      media item's year and title values. Returns score [0, 100].
      Search item scores 100 when:
        - it's first on the list of results; AND
        - it equals to the media title (ignoring case) OR all media title words are found in the search item; AND
        - search item year equals to media year.

      For now, our title scoring is pretty simple - we check if individual words
      from media item's title are found in the title from search results.
      We should also take into consideration order of words, so that "One Two" would not
      have the same score as "Two One".
  """
  Log.Debug('comparing "%s"-%s with "%s"-%s...' % (str(mediaName), str(mediaYear), str(title), str(year)))
  # Max score is when both title and year match exactly.
  score = 100

  # Item order penalty (the lower it is on the list or results, the larger the penalty).
  score = score - (itemIndex * SCORE_PENALTY_ITEM_ORDER)

  if str(mediaYear) != str(year):
    score = score - SCORE_PENALTY_YEAR_WRONG
  mediaName = mediaName.lower()
  title = title.lower()
  if mediaName != title:
    # Look for title word matches.
    words = mediaName.split()
    wordMatches = 0
    encodedTitle = title.encode(ENCODING_PLEX)
    for word in words:
      # FYI, using '\b' was troublesome (because of string encoding issues, I think).
      matcher = re.compile('^(|.*[\W«])%s([\W»].*|)$' % word.encode(ENCODING_PLEX), re.UNICODE)
      if matcher.search(encodedTitle) is not None:
        wordMatches += 1
    wordMatchesScore = float(wordMatches) / len(words)
    score = score - ((float(1) - wordMatchesScore) * SCORE_PENALTY_NO_MATCH)

  # IMPORTANT: always return an int.
  score = int(score)
  Log.Debug('***** title scored %d' % score)
  return score


def scoreThumbnailResults(thumbnailList, isPoster):
  for thumb in thumbnailList:
    Log.Debug('-------Scoring image %sx%s with index %d:\nfull image URL: "%s"\nthumb image URL: %s' %
                    (str(thumb.fullImgWidth), str(thumb.fullImgHeight), thumb.index, str(thumb.fullImgUrl), str(thumb.thumbImgUrl)))
    score = 0
    if thumb.fullImgUrl is None:
      thumb.score = 0
      continue

    if thumb.index < IMAGE_SCORE_MAX_NUMBER_OF_ITEMS:
      # Score bonus from index for items below 10 on the list.
      bonus = IMAGE_SCORE_ITEM_ORDER_BONUS_MAX * \
          ((IMAGE_SCORE_MAX_NUMBER_OF_ITEMS - thumb.index) / float(IMAGE_SCORE_MAX_NUMBER_OF_ITEMS))
      Log.Debug('++++ adding order bonus: +%s' % str(bonus))
      score += bonus

    if thumb.fullImgWidth is not None and thumb.fullImgHeight is not None:
      # Get a resolution bonus if width*height is more than a certain min value.
      if isPoster:
        minPx = POSTER_SCORE_MIN_RESOLUTION_PX
        maxPx = POSTER_SCORE_MAX_RESOLUTION_PX
        bestRatio = POSTER_SCORE_BEST_RATIO
      else:
        minPx = ART_SCORE_MIN_RESOLUTION_PX
        maxPx = ART_SCORE_MAX_RESOLUTION_PX
        bestRatio = ART_SCORE_BEST_RATIO
      pixelsCount = thumb.fullImgWidth * thumb.fullImgHeight
      if pixelsCount > minPx:
        if pixelsCount > maxPx:
          pixelsCount = maxPx
        bonus = float(IMAGE_SCORE_RESOLUTION_BONUS_MAX) * \
            float((pixelsCount - minPx)) / float((maxPx - minPx))
        Log.Debug('++++ adding resolution bonus: +%s' % str(bonus))
        score += bonus
      else:
        Log.Debug('++++ no resolution bonus for %dx%d' % (thumb.fullImgWidth, thumb.fullImgHeight))

      # Get an orientation (Portrait vs Landscape) bonus. (we prefer images that are have portrait orientation.
      ratio = thumb.fullImgWidth / float(thumb.fullImgHeight)
      radioDiff = math.fabs(bestRatio - ratio)
      if radioDiff < 0.5:
        bonus = IMAGE_SCORE_RATIO_BONUS_MAX * (0.5 - radioDiff) * 2.0
        Log.Debug('++++ adding "%s" ratio bonus: +%s' % (str(ratio), str(bonus)))
        score += bonus
      else:
        # Ignoring Landscape ratios.
        Log.Debug('++++ no ratio bonus for %dx%d' % (thumb.fullImgWidth, thumb.fullImgHeight))
    else:
      Log.Debug('++++ no size set - no resolution and no ratio bonus')

    # Get a bonus if image has a separate thumbnail URL.
    if thumb.thumbImgUrl is not None and thumb.fullImgUrl != thumb.thumbImgUrl:
      Log.Debug('++++ adding thumbnail bonus: +%d' % IMAGE_SCORE_THUMB_BONUS)
      score += IMAGE_SCORE_THUMB_BONUS

    Log.Debug('--------- SCORE: %d' % int(score))
    thumb.score = int(score)
