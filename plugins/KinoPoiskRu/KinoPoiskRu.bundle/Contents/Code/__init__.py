# -*- coding: utf-8 -*-
#
# Russian metadata plugin for Plex, which uses http://www.kinopoisk.ru/ to get the tag data.
# Плагин для обновления информации о фильмах использующий КиноПоиск (http://www.kinopoisk.ru/).
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
# @author ptath
# @author Stillness-2
# @author zhenya (Yevgeny Nyden)
#
# @version @PLUGIN.REVISION@
# @revision @REPOSITORY.REVISION@

import datetime, string, re, time, math, operator, unicodedata, hashlib, urllib
import common, tmdb, pageparser, pluginsettings as S


LOGGER = Log
IS_DEBUG = False # TODO - DON'T FORGET TO SET IT TO FALSE FOR A DISTRO.

# Compiled regex matchers. TODO: move it to a pageparser?
MATCHER_MOVIE_DURATION = re.compile('\s*(\d+).*?', re.UNICODE | re.DOTALL)
MATCHER_WIDTH_FROM_STYLE = re.compile('.*width\s*:\s*(\d+)px.*', re.UNICODE)
MATCHER_HEIGHT_FROM_STYLE = re.compile('.*height\s*:\s*(\d+)px.*', re.UNICODE)


# Plugin preferences.
# When changing default values here, also update the DefaultPrefs.json file.
PREFS = common.Preferences(
  (None, None),
  ('kinopoisk_pref_max_posters', S.KINOPOISK_PREF_DEFAULT_MAX_POSTERS),
  ('kinopoisk_pref_max_art', S.KINOPOISK_PREF_DEFAULT_MAX_ART),
  ('kinopoisk_pref_get_all_actors', S.KINOPOISK_PREF_DEFAULT_GET_ALL_ACTORS),
  ('kinopoisk_pref_imdb_support', S.KINOPOISK_PREF_DEFAULT_IMDB_SUPPORT),
  (None, None),
  ('kinopoisk_pref_imdb_rating', S.KINOPOISK_PREF_DEFAULT_IMDB_RATING),
  ('kinopoisk_pref_kp_rating', S.KINOPOISK_PREF_DEFAULT_KP_RATING))


def Start():
  LOGGER.Info('***** START ***** %s' % common.USER_AGENT)
  PREFS.readPluginPreferences()


def ValidatePrefs():
  LOGGER.Info('***** updating preferences...')
  PREFS.readPluginPreferences()


class KinoPoiskRuAgent(Agent.Movies):
  name = 'KinoPoiskRu'
  languages = [Locale.Language.Russian]
  primary_provider = True
  fallback_agent = False
  accepts_from = ['com.plexapp.agents.localmedia']
  contributes_to = None


  ##############################################################################
  ############################# S E A R C H ####################################
  ##############################################################################
  def search(self, results, media, lang, manual=False):
    """ Searches for matches on KinoPoisk using the title and year
        passed via the media object. All matches are saved in a list of results
        as MetadataSearchResult objects. For each results, we determine a
        page id, title, year, and the score (how good we think the match
        is on the scale of 1 - 100).
    """
    LOGGER.Debug('SEARCH START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    mediaName = media.name
    mediaYear = media.year
    LOGGER.Debug('searching for name="%s", year="%s", guid="%s", hash="%s"...' %
        (str(mediaName), str(mediaYear), str(media.guid), str(media.hash)))
    # Получаем страницу поиска
    LOGGER.Debug('quering kinopoisk...')

    encodedName = urllib.quote(mediaName.encode(S.ENCODING_KINOPOISK_PAGE))
    LOGGER.Debug('Loading page "%s"' % encodedName)
    page = common.getElementFromHttpRequest(S.KINOPOISK_SEARCH % encodedName, S.ENCODING_KINOPOISK_PAGE)

    if page is None:
      LOGGER.Warn('nothing was found on kinopoisk for media name "%s"' % mediaName)
    else:
      # Если страница получена, берем с нее перечень всех названий фильмов.
      LOGGER.Debug('got a kinopoisk page to parse...')
      divInfoElems = page.xpath('//self::div[@class="info"]/p[@class="name"]/a[contains(@href,"/level/1/film/")]/..')
      itemIndex = 0
      altTitle = None
      if len(divInfoElems):
        LOGGER.Debug('found %d results' % len(divInfoElems))
        for divInfoElem in divInfoElems:
          try:
            anchorFilmElem = divInfoElem.xpath('./a[contains(@href,"/level/1/film/")]/attribute::href')
            if len(anchorFilmElem):
              # Parse kinopoisk movie title id, title and year.
              match = re.search('\/film\/(.+?)\/', anchorFilmElem[0])
              if match is None:
                LOGGER.Error('unable to parse movie title id')
              else:
                kinoPoiskId = match.groups(1)[0]
                title = common.getXpathRequiredNode(divInfoElem, './/a[contains(@href,"/level/1/film/")]/text()')
                year = common.getXpathOptionalNode(divInfoElem, './/span[@class="year"]/text()')
                # Try to parse the alternative (original) title. Ignore failures.
                # This is a <span> below the title <a> tag.
                try:
                  altTitle = common.getXpathOptionalNode(divInfoElem, '../span[1]/text()')
                  if altTitle is not None:
                    altTitle = altTitle.split(',')[0].strip()
                except:
                  pass
                score = common.scoreMediaTitleMatch(mediaName, mediaYear, title, altTitle, year, itemIndex)
                results.Append(MetadataSearchResult(id=kinoPoiskId, name=title, year=year, lang=lang, score=score))
            else:
              LOGGER.Warn('unable to find film anchor elements for title "%s"' % mediaName)
          except:
            common.logException('failed to parse div.info container')
          itemIndex += 1
      else:
        LOGGER.Warn('nothing was found on kinopoisk for media name "%s"' % mediaName)
        # TODO(zhenya): investigate if we need this clause at all (haven't seen this happening).
        # Если не нашли там текст названия, значит сайт сразу дал нам страницу с фильмом (хочется верить =)
        try:
          title = page.xpath('//h1[@class="moviename-big"]/text()')[0].strip()
          kinoPoiskId = re.search('\/film\/(.+?)\/', page.xpath('.//link[contains(@href, "/film/")]/attribute::href')[0]).groups(0)[0]
          year = page.xpath('//a[contains(@href,"year")]/text()')[0].strip()
          score = common.scoreMediaTitleMatch(mediaName, mediaYear, title, altTitle, year, itemIndex)
          results.Append(MetadataSearchResult(id=kinoPoiskId, name=title, year=year, lang=lang, score=score))
        except:
          common.logException('failed to parse a KinoPoisk page')

    # Sort results according to their score (Сортируем результаты).
    results.Sort('score', descending=True)
    if IS_DEBUG:
      common.printSearchResults(results)
    LOGGER.Debug('SEARCH END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')


  ##############################################################################
  ############################# U P D A T E ####################################
  ##############################################################################
  def update(self, metadata, media, lang, force=False):
    """Updates the media title provided a KinoPoisk movie title id (metadata.guid).
       This method fetches an appropriate KinoPoisk page, parses it, and populates
       the passed media item record.
    """
    LOGGER.Debug('UPDATE START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    part = media.items[0].parts[0]
    filename = part.file.decode(common.ENCODING_PLEX)
    LOGGER.Debug('filename="%s", guid="%s"' % (filename, metadata.guid))

    matcher = re.compile(r'//(\d+)\?')
    match = matcher.search(metadata.guid)
    if match is None:
      LOGGER.Error('KinoPoisk movie title id is not specified!')
      raise Exception('ERROR: KinoPoisk movie title id is required!')
    else:
      kinoPoiskId = match.groups(1)[0]
    LOGGER.Debug('parsed KinoPoisk movie title id: "%s"' % kinoPoiskId)

    self.updateMediaItem(metadata, kinoPoiskId)

    if PREFS.imdbSupport:
      imdbId = tmdb.findBestTitleMatch(metadata.title, metadata.year, lang)
      if imdbId is not None:
        metadata.id = imdbId
    LOGGER.Debug('UPDATE END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')


  def updateMediaItem(self, metadata, kinoPoiskId):
    titlePage =  common.getElementFromHttpRequest(S.KINOPOISK_TITLE_PAGE_URL % kinoPoiskId, S.ENCODING_KINOPOISK_PAGE)
    if titlePage is not None:
      LOGGER.Debug('got a KinoPoisk page for movie title id: "%s"' % kinoPoiskId)
      try:
        resetMediaMetadata(metadata)
        parseTitleInfo(titlePage, metadata)                                       # Title. Название на русском языке.
        parseOriginalTitleInfo(titlePage, metadata)                               # Original title. Название на оригинальном языке.
        parseSummaryInfo(titlePage, metadata)                                     # Summary. Описание.
        parseRatingInfo(titlePage, metadata, kinoPoiskId)                         # Rating. Рейтинг.
        parseInfoTableTagAndUpdateMetadata(titlePage, metadata)
        parseIMDbRatingInfo(titlePage, metadata, kinoPoiskId)                     # IMDB Rating. Рейтинг IMDB берется со страницы на кинопоиске
        parseExtendedRatingInfo(titlePage, metadata, kinoPoiskId)                 # kinopoisk Rating. Информация о рейтинге с количеством голосов
        parseStudioInfo(metadata, kinoPoiskId)                                    # Studio. Студия.
        parsePeoplePageInfo(titlePage, metadata, kinoPoiskId)                     # Actors, etc. Актёры. др.
        parsePostersInfo(metadata, kinoPoiskId)                                   # Posters. Постеры.
        parseBackgroundArtInfo(metadata, kinoPoiskId)                             # Background art. Задники.
      except:
        common.logException('failed to update metadata for id %s' % kinoPoiskId)


def parseInfoTableTagAndUpdateMetadata(page, metadata):
  """ Parses the main info <table> tag, which we find by
      a css classname "info".
  """
  mainInfoTagRows = page.xpath('//table[@class="info"]/tr')
  LOGGER.Debug('parsed %d rows from the main info table tag' % len(mainInfoTagRows))
  for infoRowElem in mainInfoTagRows:
    headerTypeElem =  infoRowElem.xpath('./td[@class="type"]/text()')
    if len(headerTypeElem) != 1:
      continue
    rowTypeKey = headerTypeElem[0]
    if rowTypeKey == u'режиссер' or rowTypeKey == u'директор фильма':
      parseDirectorsInfo(infoRowElem, metadata)             # Director. Режиссер.
    elif rowTypeKey == u'год':
      parseYearInfo(infoRowElem, metadata)                  # Year. Год.
    elif rowTypeKey == u'сценарий':
      parseWritersInfo(infoRowElem, metadata)               # Writers. Сценаристы.
    elif rowTypeKey == u'жанр':
      parseGenresInfo(infoRowElem, metadata)                # Genre. Жанры.
    elif rowTypeKey == u'слоган':
      parseTaglineInfo(infoRowElem, metadata)               # Tagline. Слоган.
    elif rowTypeKey == u'рейтинг MPAA':
      parseContentRatingInfo(infoRowElem, metadata)         # Content rating. Рейтинг MPAA.
    elif rowTypeKey == u'время':
      parseDurationInfo(infoRowElem, metadata)              # Duration. Время.
    elif rowTypeKey == u'премьера (мир)':
      parseOriginallyAvailableInfo(infoRowElem, metadata)   # Originally available. Премьера в мире.
    elif rowTypeKey == u'страна':
      parseCountryInfo(infoRowElem, metadata)               # Country.
    elif rowTypeKey == u'продюсер' or \
         rowTypeKey == u'оператор' or \
         rowTypeKey == u'композитор' or \
         rowTypeKey == u'художник' or \
         rowTypeKey == u'монтаж' or \
         rowTypeKey == u'бюджет' or \
         rowTypeKey == u'сборы в США' or \
         rowTypeKey == u'релиз на DVD' or \
         rowTypeKey == u'зрители' or \
         rowTypeKey == u'монтаж':
      # These tags are not supported yet.
      # TODO(zhenya): add some of these to the summary.
      LOGGER.Debug('skipping an unsupported row: %s' % rowTypeKey)
      pass
    else:
      LOGGER.Warn('UNRECOGNIZED row type: %s' % rowTypeKey)


def parseTitleInfo(page, metadata):
  title = page.xpath('//h1[@class="moviename-big"]/text()')[0].strip()
  if len(title):
    title = title.strip('- ')
    LOGGER.Debug(' ... parsed title: "%s"' % title)
    metadata.title = title


def parseOriginalTitleInfo(page, metadata):
  origTitle = page.xpath('//span[@style="color: #666; font-size: 13px"]/text()')
  if len(origTitle):
    origTitle = ' '.join(origTitle)
    origTitle = sanitizeString(origTitle).strip('- ')
    LOGGER.Debug(' ... parsed original title: "%s"' % origTitle)
    metadata.original_title = origTitle


def parseMainActorsFromLanding(page):
  actorsMap = []
  actors = page.xpath('//td[@class="actor_list"]/div/span')
  LOGGER.Debug(' ... parsed %d actor tags' % len(actors))
  for actorSpanTag in actors:
#    actorList = actorSpanTag.xpath('./a[contains(@href,"/level/4/people/")]/text()')
    actorList = actorSpanTag.xpath('./a/text()')
    if len(actorList):
      for actor in actorList:
        if actor != u'...':
          LOGGER.Debug(' . . . . main actor: "%s"' % actor)
          actorsMap.append(actor)
  return actorsMap


def parseSummaryInfo(page, metadata):
  summaryParts = page.xpath('//div[@class="block_left_padtop"]/table/tr/td/table/tr/td/span[@class="_reachbanner_"]/div/text()')
  if len(summaryParts):
    summary = ' '.join(summaryParts)
    summary = sanitizeString(summary).strip()
    LOGGER.Debug(' ... parsed summary: "%s..."' % summary[:30])
    metadata.summary = summary


def parseRatingInfo(page, metadata, kinoPoiskId):
  try:
    ratingText = common.getXpathOptionalNode(page, './/*[@id="block_rating"]/div[1]/div[1]/a/span[1]/text()')
    if ratingText:
      metadata.rating = float(ratingText)
      LOGGER.Debug(' ... parsed rating "%s"' % ratingText)
  except:
    common.logException('unable to parse rating')


def parseIMDbRatingInfo(page, metadata, kinoPoiskId):
  try:
    if PREFS.imdbRating:
      ratingIMDbText = common.getXpathOptionalNode(page, './/*[@class="block_2"]/div[2]/text()')
      if ratingIMDbText and len(ratingIMDbText) < 50: # Sanity check.
        metadata.summary = ratingIMDbText + '. ' + metadata.summary
        LOGGER.Debug(' ... parsed IMDb rating "%s"' % ratingIMDbText)
  except:
    common.logException('unable to parse IMDb rating')


def parseExtendedRatingInfo(page, metadata, kinoPoiskId):
  try:
    if PREFS.additionalRating:
      ratingText1 = common.getXpathOptionalNode(page, './/*[@id="block_rating"]/div[1]/div[1]/a/span[1]/text()')
      ratingText2 = common.getXpathOptionalNode(page, './/*[@id="block_rating"]/div[1]/div[1]/a/span[2]/text()')
      if ratingText1 and len(ratingText1) < 50: # Sanity check.
        ratingText = 'КиноПоиск ' + ratingText1
        if ratingText2 and len(ratingText2) < 50: # Sanity check.
          ratingText = ratingText + ' (' + ratingText2 + ')'
        metadata.summary = ratingText + '. ' + metadata.summary
        LOGGER.Debug(' ... parsed extended kinopoisk rating 1="%s", 2="%s"' % (str(ratingText1), str(ratingText2)))
  except:
    common.logException('unable to parse extended kinopoisk rating')


def parseStudioInfo(metadata, kinoPoiskId):
  page = common.getElementFromHttpRequest(S.KINOPOISK_STUDIO % kinoPoiskId, S.ENCODING_KINOPOISK_PAGE)
  if not page:
    return
  studios = page.xpath(u'//table/tr/td[b="Производство:"]/../following-sibling::tr/td/a/text()')
  if len(studios):
    # Берем только первую студию.
    studio = studios[0].strip()
    LOGGER.Debug(' ... parsed studio: %s' % studio)
    metadata.studio = studio


def parseDirectorsInfo(infoRowElem, metadata):
  directors = infoRowElem.xpath('.//a/text()')
  LOGGER.Debug(' ... parsed %d director tags' % len(directors))
  if len(directors):
    for director in directors:
      if director != u'...':
        LOGGER.Debug(' . . . . director: "%s"' % director)
        metadata.directors.add(director)


def parseYearInfo(infoRowElem, metadata):
  try:
    yearText = infoRowElem.xpath('.//a/text()')
    if len(yearText):
      LOGGER.Debug(' ... parsed year: %s' % yearText[0])
      metadata.year = int(yearText[0])
  except:
    common.logException('unable to parse year')


def parseWritersInfo(infoRowElem, metadata):
  writers = infoRowElem.xpath('.//a/text()')
  LOGGER.Debug(' ... parsed %d writer tags' % len(writers))
  if len(writers):
    for writer in writers:
      if writer != u'...':
        LOGGER.Debug(' . . . . writer "%s"' % writer)
        metadata.writers.add(writer)


def parseGenresInfo(infoRowElem, metadata):
  genres = infoRowElem.xpath('.//a/text()')
  LOGGER.Debug(' ... parsed %d genre tags' % len(genres))
  if len(genres):
    for genre in genres:
      if genre != u'...':
        genre = genre.capitalize()
        LOGGER.Debug(' . . . . genre: "%s"' % genre)
        metadata.genres.add(genre)


def parseTaglineInfo(infoRowElem, metadata):
  taglineParts = infoRowElem.xpath('./td[@style]/text()')
  if len(taglineParts):
    tagline = ' '.join(taglineParts)
    tagline = sanitizeString(tagline)
    tagline = tagline.strip('- ')
    LOGGER.Debug(' ... parsed tagline: "%s"' % tagline[:20])
    metadata.tagline = tagline


def parseContentRatingInfo(infoRowElem, metadata):
  metadata.content_rating = None
  contentRatingElems = infoRowElem.xpath('.//a/img/attribute::src')
  if len(contentRatingElems) == 1:
    match = re.search('\/([^/.]+?)\.gif$',contentRatingElems[0])
    if match is not None:
      contentRating = match.groups(1)[0]
      LOGGER.Debug(' ... parsed content rating: "%s"' % str(contentRating))
      metadata.content_rating = contentRating


def parseDurationInfo(infoRowElem, metadata):
  try:
    durationElems = infoRowElem.xpath('./td[@class="time"]/text()')
    if len(durationElems) > 0:
      match = MATCHER_MOVIE_DURATION.search(durationElems[0])
      if match is not None:
        duration = int(int(match.groups(1)[0])) * 1000 * 60
        LOGGER.Debug(' ... parsed duration: "%s"' % str(duration))
        metadata.duration = duration
  except:
    common.logException('unable to parse duration')


def parseOriginallyAvailableInfo(infoRowElem, metadata):
  try:
    originalDateElems = infoRowElem.xpath('.//a/text()')
    if len(originalDateElems):
      (dd, mm, yy) = originalDateElems[0].split()
      if len(dd) == 1:
        dd = '0' + dd
      mm = S.RU_MONTH[mm]
      originalDate = Datetime.ParseDate(yy + '-' + mm + '-' + dd).date()
      LOGGER.Debug(' ... parsed originally available date: "%s"' % str(originalDate))
      metadata.originally_available_at = originalDate
  except:
    common.logException('unable to parse originally available date')


def parseCountryInfo(infoRowElem, metadata):
  countries = common.getXpathOptionalNodeStrings(infoRowElem, './/a/text()')
  for country in countries:
    metadata.countries.add(country)
    LOGGER.Debug(' . . . . country: "%s"' % str(country))
  if not len(countries):
    LOGGER.Debug(' . . . . countries: NONE')


def parsePeoplePageInfo(titlePage, metadata, kinoPoiskId):
  """ Parses people - mostly actors. Here (on this page)
      we have access to extensive information about all who participated in
      creating this movie.
  """
  # Parse a dedicated 'people' page.
  parseAllActors = PREFS.getAllActors
  page = common.getElementFromHttpRequest(S.KINOPOISK_PEOPLE % kinoPoiskId, S.ENCODING_KINOPOISK_PAGE)

  data = pageparser.PeopleParser(LOGGER).parse(page, parseAllActors)
  actorRoles = data['actors']

  # Parse main actors from the main title page.
  mainActors = parseMainActorsFromLanding(titlePage)
  actors = []
  for mainActor in mainActors:
    i = 0
    while i < len(actorRoles):
      actorRole = actorRoles[i]
      if actorRole[0] == mainActor:
        actors.append((mainActor, actorRole[1]))
        del actorRoles[i]
        break
      i = i + 1

  # Adding main actors that were found on the 'people' page.
  for personName, roleName in actors:
    addActorToMetadata(metadata, personName, roleName)
  for personName, roleName in actorRoles:
    addActorToMetadata(metadata, personName, roleName)


def addActorToMetadata(metadata, actorName, roleName):
  role = metadata.roles.new()
  role.actor = actorName
  if roleName is not None and roleName != '':
    role.role = roleName
  LOGGER.Debug(' . . . actor/role: ' + actorName + ' => ' + str(roleName))


def parsePostersInfo(metadata, kinoPoiskId):
  """ Fetches and populates posters metadata.
      Получение адресов постеров.
  """
  LOGGER.Debug('===== loading P O S T E R S ===== for title id "%s"...' % str(kinoPoiskId))
  if PREFS.maxPosters == 0:
    LOGGER.Debug(' ... SKIPPED.')
    metadata.posters.validate_keys([])
    return

  # Получение ярлыка (большого если есть или маленького с главной страницы).
  thumb = getPosterThumbnailBigOrSmall(kinoPoiskId)

  # Getting images data frpm poster pages if more than 1 poster is requested.
  posterPages = None
  if PREFS.maxPosters > 1:
    maxPages = 1
    if PREFS.maxPosters >= 20:
      maxPages = 2 # Even this is an extreme case, we should need too many pages.
    posterPages = fetchImageDataPages(S.KINOPOISK_POSTERS, kinoPoiskId, maxPages)

  # Получение URL постеров.
  updateImageMetadata(posterPages, metadata, PREFS.maxPosters, True, thumb)


def parseBackgroundArtInfo(metadata, kinoPoiskId):
  """ Fetches and populates background art metadata.
      Получение адресов задников.
  """
  LOGGER.Debug('===== loading B A C K G R O U N D  A R T ===== for title id "%s"...' % str(kinoPoiskId))
  if PREFS.maxArt == 0:
    LOGGER.Debug(' ... SKIPPED.')
    metadata.art.validate_keys([])
    return

  maxPages = 1
  if PREFS.maxArt >= 20:
    maxPages = 2 # Even this is an extreme case, we should need too many pages.
  artPages = fetchImageDataPages(S.KINOPOISK_ART, kinoPoiskId, maxPages)
  if not len(artPages):
    LOGGER.Debug(' ... determined NO background art URLs')
    return

  # Получение урлов задников.
  updateImageMetadata(artPages, metadata, PREFS.maxArt, False, None)


def resetMediaMetadata(metadata):
  metadata.genres.clear()
  metadata.directors.clear()
  metadata.writers.clear()
  metadata.roles.clear()
  metadata.countries.clear()
  metadata.collections.clear()
  metadata.studio = ''
  metadata.summary = ''
  metadata.title = ''
#        metadata.trivia = ''
#        metadata.quotes = ''
  metadata.year = None
  metadata.originally_available_at = None
  metadata.original_title = ''
  metadata.duration = None


def sanitizeString(msg):
  """ Функция для замены специальных символов.
  """
  res = msg.replace(u'\x85', u'...')
  res = res.replace(u'\x97', u'-')
  return res


def ensureAbsoluteUrl(url):
  """ Returns an absolute URL (starts with http://)
      pre-pending base kinoposk URL to the passed URL when necessary.
  """
  if url is None or len(url.strip()) < 10:
    return None
  url = url.strip()
  if url[0:4] == 'http':
    return url
  return S.KINOPOISK_SITE_BASE + url.lstrip('/')


def parseXpathElementValue(elem, path):
  values = elem.xpath(path)
  if len(values):
    return values[0]
  return None


def updateImageMetadata(pages, metadata, maxImages, isPoster, thumb):
  thumbnailList = []
  if thumb is not None:
    thumbnailList.append(thumb)
  if maxImages > 1:
    # Parsing URLs from the passed pages.
    maxImagesToParse = maxImages - len(thumbnailList) + 2 # Give it a couple of extras to choose from.
    for page in pages:
      maxImagesToParse = parseImageDataFromPhotoTableTag(page, thumbnailList, isPoster, maxImagesToParse)
      if not maxImagesToParse:
        break

  # Sort results according to their score and chop out extraneous images. Сортируем результаты.
  thumbnailList = sorted(thumbnailList, key=lambda t : t.score, reverse=True)[0:maxImages]
  if IS_DEBUG:
    common.printImageSearchResults(thumbnailList)

  # Now, walk over the top N (<max) results and update metadata.
  if isPoster:
    imagesContainer = metadata.posters
  else:
    imagesContainer = metadata.art
  index = 0
  validNames = list()
  for result in thumbnailList:
    if result.thumbImgUrl is None:
      img = result.fullImgUrl
    else:
      img = result.thumbImgUrl
    try:
      imagesContainer[result.fullImgUrl] = Proxy.Preview(HTTP.Request(img), sort_order = index)
      validNames.append(result.fullImgUrl)
      index += 1
    except:
      common.logException('Error generating preview for: "%s".' % str(img))
  imagesContainer.validate_keys(validNames)


def fetchImageDataPages(urlTemplate, kinoPoiskId, maxPages):
  pages = []
  page = common.getElementFromHttpRequest(urlTemplate % (kinoPoiskId, 1), S.ENCODING_KINOPOISK_PAGE)
  if page is not None:
    pages.append(page)
    if maxPages > 1:
      anchorElems = page.xpath('//div[@class="navigator"]/ul/li[@class="arr"]/a')
      if len(anchorElems):
        nav = parseXpathElementValue(anchorElems[-1], './attribute::href')
        match = re.search('page\/(\d+?)\/$', nav)
        if match is not None:
          try:
            for pageIndex in range(2, int(match.groups(1)[0]) + 1):
              page =  common.getElementFromHttpRequest(urlTemplate % (kinoPoiskId, pageIndex), S.ENCODING_KINOPOISK_PAGE)
              if page is not None:
                pages.append(page)
                if pageIndex == maxPages:
                  break
          except:
            common.logException('unable to parse image art page')
  return pages


def parseImageDataFromPhotoTableTag(page, thumbnailList, isPoster, maxImagesToParse):
  anchorElems = page.xpath('//table[@class="fotos" or @class="fotos fotos1" or @class="fotos fotos2"]/tr/td/a')
  currItemIndex = len(thumbnailList)
  for anchorElem in anchorElems:
    thumb = None
    try:
      thumb = parseImageDataFromAnchorElement(anchorElem, currItemIndex)
      currItemIndex += 1
    except:
      common.logException('unable to parse image URLs')
    if thumb is None:
      LOGGER.Debug('no URLs - skipping an image')
      continue
    else:
      common.scoreThumbnailResult(thumb, isPoster)
      if PREFS.imageChoice == common.IMAGE_CHOICE_BEST and \
         thumb.score < common.IMAGE_SCORE_BEST_THRESHOLD:
        continue
      thumbnailList.append(thumb)
      LOGGER.Debug('GOT URLs for an image: index=%d, thumb="%s", full="%s" (%sx%s)' %
          (thumb.index, str(thumb.thumbImgUrl), str(thumb.fullImgUrl),
          str(thumb.fullImgWidth), str(thumb.fullImgHeight)))
      maxImagesToParse = maxImagesToParse - 1
      if not maxImagesToParse:
        break
  return maxImagesToParse


def parseImageDataFromAnchorElement(anchorElem, index):
  thumbSizeUrl = None
  fullSizeUrl = None
  fullSizeDimensions = None, None
  fullSizeProxyPageUrl = anchorElem.get('href')
  thumbSizeImgElem = parseXpathElementValue(anchorElem, './img')
  if thumbSizeImgElem is not None:
    thumbSizeUrl = thumbSizeImgElem.get('src')
    if thumbSizeUrl is not None:
      thumbSizeUrl = ensureAbsoluteUrl(thumbSizeUrl)

  if fullSizeProxyPageUrl is not None:
    fullSizeProxyPage = common.getElementFromHttpRequest(ensureAbsoluteUrl(fullSizeProxyPageUrl), S.ENCODING_KINOPOISK_PAGE)
    if fullSizeProxyPage is not None:
      imageElem = parseXpathElementValue(fullSizeProxyPage, '//img[@id="image"]')
      if imageElem is not None:
        fullSizeUrl = imageElem.get('src')
        fullSizeDimensions = parseImageElemDimensions(imageElem)

  # If we have no full size image URL, we could use the thumb's.
  if fullSizeUrl is None and thumbSizeUrl is not None:
      LOGGER.Debug('found no full size image, will use the thumbnail')
      fullSizeUrl = thumbSizeUrl

  if fullSizeUrl is None and thumbSizeUrl is None:
    return None
  return common.Thumbnail(thumbSizeUrl,
    ensureAbsoluteUrl(fullSizeUrl),
    fullSizeDimensions[0],
    fullSizeDimensions[1],
    index,
    0) # Initial score.


def parseImageElemDimensions(imageElem):
  """ Determines dimensions of a given image element and returns it as a (width, height) tuple,
      where width and height are of type int or None.
  """
  style = imageElem.get('style')
  width = imageElem.get('width')
  if width is None and style is not None:
    match = MATCHER_WIDTH_FROM_STYLE.search(style)
    if match is not None:
      width = match.groups()[0]
  height = imageElem.get('height')
  if height is None and style is not None:
    match = MATCHER_HEIGHT_FROM_STYLE.search(style)
    if match is not None:
      height = match.groups()[0]
  if width is not None:
    width = int(width)
  if height is not None:
    height = int(height)
  return width, height


def getPosterThumbnailBigOrSmall(kinoPoiskId):
  LOGGER.Debug(' * parsing thumbnail...')
  thumb = None
  try:
    bigImgThumbUrl = S.KINOPOISK_MOVIE_BIG_THUMBNAIL % kinoPoiskId
    response = common.getResponseFromHttpRequest(bigImgThumbUrl)
    if response is not None:
      contentType = response.headers['content-type']
      if 'image/jpeg' == contentType:
        LOGGER.Debug(' * found BIG thumb')
        thumb = common.Thumbnail(None,
          bigImgThumbUrl,
          S.KINOPOISK_MOVIE_THUMBNAIL_DEFAULT_WIDTH,
          S.KINOPOISK_MOVIE_THUMBNAIL_DEFAULT_HEIGHT,
          0, # Index.
          1000) # Big thumb should have the highest initial score.
      else:
        LOGGER.Debug(' * BIG thumb is NOT found')
  except:
    LOGGER.Debug(' * UNABLE to fetch BIG thumb')
    if IS_DEBUG:
      common.logException('failed to fetch BIG thumb')

  if thumb is None:
    LOGGER.Debug(' * adding default (SMALL) thumb')
    # If there is no big title, add a small one.
    thumb = common.Thumbnail(None,
      S.KINOPOISK_MOVIE_THUMBNAIL % kinoPoiskId,
      S.KINOPOISK_MOVIE_THUMBNAIL_WIDTH,
      S.KINOPOISK_MOVIE_THUMBNAIL_HEIGHT,
      0, # Index.
      0) # Initial score.

  return thumb