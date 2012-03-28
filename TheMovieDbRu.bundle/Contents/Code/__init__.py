# -*- coding: utf-8 -*-
# TheMoviesDB
# Multi-language support added by Aqntbghd

# TODO : Deal with languages AND locations as TMDB makes the difference between them.
# TODO : Deal with TMDB set of films as collections as soon as the API is made public

import time

# TODO - ----------------------------- - - - - - - -- search for a movie - can't use hash?
# http://api.themoviedb.org/2.1/methods/Movie.search
# http://api.themoviedb.org/2.1/Movie.search/ru/xml/a3dc111e66105f6387e99393813ae4d5/%s
TMDB_GETINFO_IMDB = 'http://api.themoviedb.org/2.1/Movie.imdbLookup/en/json/a3dc111e66105f6387e99393813ae4d5/%s'
TMDB_GETINFO_TMDB = 'http://api.themoviedb.org/2.1/Movie.getInfo/%s/json/a3dc111e66105f6387e99393813ae4d5/%s'
TMDB_GETINFO_HASH = 'http://api.themoviedb.org/2.1/Hash.getInfo/%s/json/a3dc111e66105f6387e99393813ae4d5/%s'


# Preference item names.
PREF_IS_DEBUG_NAME = 'tmdbru_pref_is_debug'
PREF_LOG_LEVEL_NAME = 'tmdbru_pref_log_level'
PREF_CACHE_TIME_NAME = 'tmdbru_pref_cache_time'
PREF_CACHE_TIME_DEFAULT = CACHE_1MONTH

TMDB_LANGUAGE_CODES = {
  'en': 'en',
  'ru': 'ru',
}

class LocalSettings():
  """ These instance variables are populated from plugin preferences. """
  # Current log level.
  # Supported values are: 0 = none, 1 = error, 2 = warning, 3 = info, 4 = fine, 5 = finest.
  logLevel = 1
  isDebug = False

localPrefs = LocalSettings()


def Start():
  sendToInfoLog('***** START *****')
  readPluginPreferences()


def GetLanguageCode(lang):
  if TMDB_LANGUAGE_CODES.has_key(lang):
    return TMDB_LANGUAGE_CODES[lang]
  else:
    return 'ru'


@expose
def GetImdbIdFromHash(openSubtitlesHash, lang):
  try:
    url = TMDB_GETINFO_HASH % (GetLanguageCode(lang), str(openSubtitlesHash))
    sendToFineLog('fetching URL: "%s"' % url)
    tmdb_dict = JSON.ObjectFromURL(url)[0]
    if isinstance(tmdb_dict, dict) and tmdb_dict.has_key('imdb_id'):
      sendToFineLog('got result')
      return MetadataSearchResult(
        id    = tmdb_dict['imdb_id'],
        name  = tmdb_dict['name'],
        year  = None,
        lang  = lang,
        score = 94)
    else:
      sendToFineLog('found nothin\'')
      return None

  except:
    sendToErrorLog(getExceptionInfo('Error fetching IMDB id for: "%s".' % str(openSubtitlesHash)))
    return None

class TMDbRuAgent(Agent.Movies):
  name = 'TheMovieDbRu'
  languages = [Locale.Language.Russian, Locale.Language.English]
  primary_provider = True

  def search(self, results, media, lang):
    sendToInfoLog('SEARCH START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    mediaName = media.name
    mediaYear = media.year
    sendToInfoLog('searching for name="%s", year="%s", guid="%s", hash="%s", primary_metadata="%s", openSubtitlesHash="%s"...' %
        (str(mediaName), str(mediaYear), str(media.guid), str(media.hash), str(media.primary_metadata), str(media.openSubtitlesHash)))
    sendToFinestLog('quering TMDB...')

    if media.primary_metadata is not None:
      tmdb_id = self.get_tmdb_id(media.primary_metadata.id) # get the TMDb ID using the IMDB ID
      if tmdb_id:
        results.Append(MetadataSearchResult(id = tmdb_id, score = 100))
    elif media.openSubtitlesHash is not None:
      match = GetImdbIdFromHash(media.openSubtitlesHash, lang)

    if localPrefs.logLevel >= 3:
      sendToInfoLog('search produced %d results:' % len(results))
      index = 0
      for result in results:
        sendToInfoLog(' ... result %d: id="%s", name="%s", year="%s", score="%d".' % (index, result.id, result.name, str(result.year), result.score))
        index += 1
    sendToInfoLog('SEARCH END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

  def update(self, metadata, media, lang): 
    print '++++++++++++++++ UPDATE START'
    proxy = Proxy.Preview
    try:
      tmdb_info = HTTP.Request(TMDB_GETINFO_TMDB % (GetLanguageCode(lang), metadata.id)).content
      if tmdb_info.count('503 Service Unavailable') > 0:
        time.sleep(5)
        tmdb_info = HTTP.Request(TMDB_GETINFO_TMDB % (GetLanguageCode(lang), metadata.id), cacheTime=0).content
      tmdb_dict = JSON.ObjectFromString(tmdb_info)[0] #get the full TMDB info record using the TMDB id
    except:
      Log('Exception fetching JSON from theMovieDB (1).')
      return None

    # Rating.
    votes = tmdb_dict['votes']
    rating = tmdb_dict['rating']
    if votes > 3:
      metadata.rating = rating

    # Title of the film.
    metadata.title = tmdb_dict['name']
    
    # Original Title of the film.
    metadata.original_title = tmdb_dict['original_name']
   
    # Tagline.
    metadata.tagline = tmdb_dict['tagline']

    # Content rating.
    metadata.content_rating = tmdb_dict['certification']

    # Summary.
    metadata.summary = tmdb_dict['overview']
    if metadata.summary == 'No overview found.':
      metadata.summary = ""

    # Release date.
    try: 
      metadata.originally_available_at = Datetime.ParseDate(tmdb_dict['released']).date()
      metadata.year = metadata.originally_available_at.year
    except: 
      pass

    # Runtime.
    try: metadata.duration = int(tmdb_dict['runtime']) * 60 * 1000
    except: pass

    # Genres.
    metadata.genres.clear()
    for genre in tmdb_dict['genres']:
      metadata.genres.add(genre['name'])

    # Studio.
    try: metadata.studio = tmdb_dict['studios'][0]['name']
    except: pass

    # Cast.
    metadata.directors.clear()
    metadata.writers.clear()
    metadata.roles.clear()

    for member in tmdb_dict['cast']:
      if member['job'] == 'Director':
        metadata.directors.add(member['name'])
      elif member['job'] == 'Author':
        metadata.writers.add(member['name'])
      elif member['job'] == 'Actor':
        role = metadata.roles.new()
        role.role = member['character']
        role.actor = member['name']

    i = 0
    valid_names = list()
    for p in tmdb_dict['posters']:
      if p['image']['size'] == 'original':
        i += 1
        valid_names.append(p['image']['url'])
        if p['image']['url'] not in metadata.posters:
          p_id = p['image']['id']

          # Find a thumbnail.
          for t in tmdb_dict['posters']:
            if t['image']['id'] == p_id and t['image']['size'] == 'mid':
              thumb = HTTP.Request(t['image']['url'])
              break

          try: metadata.posters[p['image']['url']] = proxy(thumb, sort_order = i)
          except: pass

    metadata.posters.validate_keys(valid_names)
    valid_names = list()

    i = 0
    for b in tmdb_dict['backdrops']:
      if b['image']['size'] == 'original':
        i += 1
        valid_names.append(b['image']['url'])
        if b['image']['url'] not in metadata.art:
          b_id = b['image']['id']
          for t in tmdb_dict['backdrops']:
            if t['image']['id'] == b_id and t['image']['size'] == 'poster':
              thumb = HTTP.Request(t['image']['url'])
              break 
          try: metadata.art[b['image']['url']] = proxy(thumb, sort_order = i)
          except: pass

    metadata.art.validate_keys(valid_names)

  def get_tmdb_id(self, imdb_id):
    try:
      tmdb_info = HTTP.Request(TMDB_GETINFO_IMDB % str(imdb_id)).content
      if tmdb_info.count('503 Service Unavailable') > 0:
        time.sleep(5)
        tmdb_info = HTTP.Request(TMDB_GETINFO_IMDB % str(imdb_id), cacheTime=0).content
      tmdb_dict = JSON.ObjectFromString(tmdb_info)[0]
    except:
      Log('Exception fetching JSON from theMovieDB (2).')
      return None
    if tmdb_dict and isinstance(tmdb_dict, dict):
      return str(tmdb_dict['id'])
    else:
      return None

def sendToFinestLog(msg):
  if localPrefs.logLevel >= 5:
    if localPrefs.isDebug:
      print 'FINEST: ' + msg
    else:
      Log.Debug(msg)


def sendToFineLog(msg):
  if localPrefs.logLevel >= 4:
    if localPrefs.isDebug:
      print 'FINE: ' + msg
    else:
      Log.Info(msg)


def sendToInfoLog(msg):
  if localPrefs.logLevel >= 3:
    if localPrefs.isDebug:
      print 'INFO: ' + msg
    else:
      Log.Debug(msg)


def sendToWarnLog(msg):
  if localPrefs.logLevel >= 2:
    if localPrefs.isDebug:
      print 'WARN: ' + msg
    else:
      Log.WARN(msg)


def sendToErrorLog(msg):
  if localPrefs.logLevel >= 1:
    if localPrefs.isDebug:
      print 'ERROR: ' + msg
    else:
      Log.ERROR(msg)

def readPluginPreferences():
  prefLogLevel = Prefs[PREF_LOG_LEVEL_NAME]
  if prefLogLevel == u'ничего':
    localPrefs.logLevel = 0
  elif prefLogLevel == u'предупреждения':
    localPrefs.logLevel = 2
  elif prefLogLevel == u'информативно':
    localPrefs.logLevel = 3
  elif prefLogLevel == u'подробно':
    localPrefs.logLevel = 4
  elif prefLogLevel == u'очень подробно':
    localPrefs.logLevel = 5
  else:
    localPrefs.logLevel = 1 # Default is error.
  localPrefs.isDebug = Prefs[PREF_IS_DEBUG_NAME]

  # Setting cache expiration time.
  prefCache = Prefs[PREF_CACHE_TIME_NAME]
  if prefCache == u'1 минута':
    cacheExp = CACHE_1MINUTE
  elif prefCache == u'1 час':
    cacheExp = CACHE_1HOUR
  elif prefCache == u'1 день':
    cacheExp = CACHE_1DAY
  elif prefCache == u'1 неделя':
    cacheExp = CACHE_1DAY
  elif prefCache == u'1 месяц':
    cacheExp = CACHE_1MONTH
  elif prefCache == u'1 год':
    cacheExp = CACHE_1MONTH * 12
  else:
    cacheExp = PREF_CACHE_TIME_DEFAULT
  HTTP.CacheTime = cacheExp

  sendToInfoLog('PREF: Setting debug to %s.' % str(localPrefs.isDebug))
  sendToInfoLog('PREF: Setting log level to %d (%s).' % (localPrefs.logLevel, prefLogLevel))
  sendToInfoLog('PREF: Setting cache expiration to %d seconds (%s).' % (cacheExp, prefCache))

def getExceptionInfo(msg):
  excInfo = sys.exc_info()
  return '%s; exception: %s; cause: %s' % (msg, excInfo[0], excInfo[1])

