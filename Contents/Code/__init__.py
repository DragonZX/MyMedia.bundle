# -*- coding: utf-8 -*-
#
# Metadata plugin for Plex, which uses local info files to get the tag data.
# Copyright (C) 2014  Yevgeny Nyden
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
# @version @PLUGIN.REVISION@
# @revision @REPOSITORY.REVISION@

import re, os, io, common, datetime, time


LOGGER = Log

MATCHER_INFO_TAG = re.compile('\s*\[(.*)\]\s*', re.UNICODE)


def Start():
  LOGGER.Info('***** START ***** %s' % common.USER_AGENT)


def ValidatePrefs():
  LOGGER.Info('***** updating preferences...')


# Only use unicode if it's supported, which it is on Windows and OS X,
# but not Linux. This allows things to work with non-ASCII characters
# without having to go through a bunch of work to ensure the Linux
# filesystem is UTF-8 "clean".
#
def unicodize(s):
  filename = s
  if os.path.supports_unicode_filenames:
    try: filename = unicode(s.decode('utf-8'))
    except: pass
  return filename

def getAndTestInfoFilePath(media):
  part = media.items[0].parts[0]
  filename = unicodize(part.file)
  path = os.path.splitext(filename)[0] + '.info'
  if os.path.exists(path):
    return path
  else:
    return None

def parsePipeSeparatedTuple(string):
  tokens = string.split('|')
  second = ''
  if len(tokens) > 1:
    second = tokens[1]
  return tokens[0], second


def writeTagValueToMetadata(metadata, tagName, tagValue):
  try:
    tagName = tagName.lower()
    tagValue = tagValue.strip()
    if tagValue == '':
      return
    if tagName == 'title':
      metadata.title = tagValue
    elif tagName == 'originaltitle':
      metadata.original_title = tagValue
    elif tagName == 'year':
      metadata.year = int(tagValue)
    elif tagName == 'tagline':
      metadata.tagline = tagValue
    elif tagName == 'summary':
      metadata.summary = tagValue
    elif tagName == 'duration':
      metadata.duration = int(tagValue) * 1000 * 60
    elif tagName == 'rating':
      metadata.rating = float(tagValue)
    elif tagName == 'contentrating':
      metadata.content_rating = tagValue
    elif tagName == 'originaldate':
      metadata.originally_available_at = Datetime.ParseDate(tagValue).date()
    elif tagName == 'country':
      metadata.countries.add(tagValue)
    elif tagName == 'genre':
      metadata.genres.add(tagValue.title())
    elif tagName == 'studio':
      metadata.studio = tagValue
    elif tagName == 'actor':
      role = metadata.roles.new()
      role.actor, role.role = parsePipeSeparatedTuple(tagValue)
    elif tagName == 'director':
      metadata.directors.add(tagValue)
    elif tagName == 'writer':
      metadata.writers.add(tagValue)
    elif tagName == 'poster':
      pass
    elif tagName == 'still':
      pass
  except:
    LOGGER.Error('Failed to parse tag "' + str(tagName) + '"')
  LOGGER.Debug('..... wrote tag "' + tagName + '" = "' + tagValue + '"...')


class MyMediaAgent(Agent.Movies):
  name = 'My Local Media (Movies)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = True
  fallback_agent = False
  accepts_from = None
  contributes_to = None


  ##############################################################################
  ############################# S E A R C H ####################################
  ##############################################################################
  def search(self, results, media, lang, manual=False):
    LOGGER.Debug('SEARCH START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    mediaName = media.name
    mediaYear = media.year
    mediaHash = media.hash
    LOGGER.Debug('searching for name="%s", year="%s", guid="%s", hash="%s"...' %
        (str(mediaName), str(mediaYear), str(media.guid), str(mediaHash)))

    path = getAndTestInfoFilePath(media)
    if path is None:
      return

    part = media.items[0].parts[0]
    if mediaHash is None:
      mediaHash = part.hash
    if mediaYear is None:
      filename = unicodize(part.file)
      modificationTime = os.path.getmtime(filename)
      date = datetime.date.fromtimestamp(modificationTime)
      mediaYear = date.year
    results.Append(MetadataSearchResult(id=mediaHash, name=mediaName, year=mediaYear, score=100, lang=lang))

    LOGGER.Debug('SEARCH END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')


  ##############################################################################
  ############################# U P D A T E ####################################
  ##############################################################################
  def update(self, metadata, media, lang, force=False):
    """
    """
    LOGGER.Debug('UPDATE START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

    # TODO(zhenya): investigate how we could set posters and backgrounds.
    # It looks like we can't use the local file system for that - so,
    # pulling files from the web might be our only choice... :-(

    # TODO(zhenya): do more testing.

    path = getAndTestInfoFilePath(media)
    if path is None:
      return

#    metadata.posters.clear()
    common.resetMediaAllMetadata(metadata)
    lastTagName = None
    lastTagValue = ''
    for infoLine in io.open(path, 'rt'):
      match = MATCHER_INFO_TAG.search(infoLine)
      if match is None:
        textToAdd = infoLine.strip()
        if textToAdd == '':
          lastTagValue += '\n\n'
        else:
          if lastTagValue != '':
            lastTagValue += ' '
          lastTagValue += textToAdd
      else:
        if lastTagName is not None:
          if lastTagName == 'posterxx':
            part = media.items[0].parts[0]
            filename = unicodize(part.file)
            posterPath = os.path.join(os.path.dirname(filename), lastTagValue)
            metadata.posters[posterPath] = Proxy.Media(io.open(posterPath, 'rb'))
            validNames = list()
            validNames.append(posterPath)
            metadata.posters.validate_keys(validNames)
            LOGGER.Debug('+ + + + + + + ' + posterPath)
          else:
            writeTagValueToMetadata(metadata, lastTagName, lastTagValue)
          lastTagValue = ''
        lastTagName = match.groups()[0]

    LOGGER.Debug('UPDATE END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

