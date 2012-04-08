VIDEO_PREFIX = "/video/weewza"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
HTBi = ''
THTi = ''
ComedyTVi = ''
DTVi = ''
####################################################################################################

def Start():

  ## make this plugin show up in the 'Video' section
  ## in Plex. The L() function pulls the string out of the strings
  ## file in the Contents/Strings/ folder in the bundle
  ## see also:
  ##  http://dev.plexapp.com/docs/mod_Plugin.html
  ##  http://dev.plexapp.com/docs/Bundle.html#the-strings-directory
  Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)

  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

  ## set some defaults so that you don't have to
  ## pass these parameters to these object types
  ## every single time
  ## see also:
  ##  http://dev.plexapp.com/docs/Objects.html
  MediaContainer.title1 = NAME
  MediaContainer.viewGroup = "List"
  MediaContainer.art = R(ART)
  DirectoryItem.thumb = R(ICON)
  VideoItem.thumb = R(ICON)
    
  HTTP.CacheTime = CACHE_1HOUR


#### the rest of these are user created functions and
#### are not reserved by the plugin framework.
#### see: http://dev.plexapp.com/docs/Functions.html for
#### a list of reserved functions above


def VideoMainMenu():
  """ Example main menu referenced in the Start() method
      for the 'Video' prefix handler.
  """

  # Container acting sort of like a folder on
  # a file system containing other things like
  # "sub-folders", videos, music, etc
  # see:
  #  http://dev.plexapp.com/docs/Objects.html#MediaContainer
  dir = MediaContainer(viewGroup="InfoList")

  # see:
  #  http://dev.plexapp.com/docs/Objects.html#DirectoryItem
  #  http://dev.plexapp.com/docs/Objects.html#function-objects
  dir.Append(WebVideoItem('http://embed.weewza.com/IJakE65q',title=u"THT", thumb=R('THTi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/agCv8wwN',title=u"ComedyTV", thumb=R('ComedyTVi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/GcIrrleE',title=u"ДТВ", thumb=R('DTVi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/r7wDuvWZ',title=u"PEH", thumb=R('PEHi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/ckNILH6G',title=u"HTB", thumb=R('HTBi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/N3yCekb9',title=u"OPT", thumb=R('ORTi.png')))
  dir.Append(VideoItem('rtsp://82.166.49.45/liveisrael9130510',title="Israel Plus", thumb=R('ISRAELPi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/rcd4PcTg',title="Russia 1", thumb=R('RUSSIA1i.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/F3WpMYoI',title="Russia 2", thumb=R('RUSSIA2i.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/gLkVoR2h',title="Russia K", thumb=R('RUSSIAKi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/t8NW9MWN',title=u"CTC", thumb=R('CTCi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/m6ow4Pc6',title=u"Вопросы и ответы", thumb=R('VIOi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/BQFYlB4l',title=u"ТВ-Бульвар", thumb=R('TVBi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/bvIPb6mc',title="Discovery World", thumb=R('DISCWi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/8emBR88X',title="Discovery Science", thumb=R('DISCSi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/S34cLkoW',title="Animal Planet", thumb=R('ANIMPi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/d1ZxVdvi',title="National Geographic", thumb=R('NATGi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/WjQRIvrN',title=u"Зоопарк", thumb=R('ZOOi.gif')))
  dir.Append(WebVideoItem('http://embed.weewza.com/ES2MfHOo',title="Explorer", thumb=R('EXPi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/BsISm2a1',title="History", thumb=R('HISi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/dWVT6fwL',title=u"Охота и рыбалка", thumb=R('OIRi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/QDy6jWDn',title=u"Телеканал усадьба", thumb=R('USADi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/q6G1eDaY',title=u"TV 1000", thumb=R('TV1000i.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/kghmXvUr',title=u"Индия ТВ", thumb=R('INTVi.gif')))
  dir.Append(WebVideoItem('http://embed.weewza.com/qgvjdyzE',title="AXN SciFi", thumb=R('AXNi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/lP5HA6t6',title="TV 1000 Action", thumb=R('TV1000Ai.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/n3EKECZr',title="SciFi", thumb=R('SCIFIi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/hHAEtdkF',title="FOX Life", thumb=R('FOXLi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/wmh5BNn4',title="Sony Entertainment", thumb=R('SONYi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/7aOXyAum',title=u"МНОГО TV", thumb=R('MNOGOi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/ibvbabbR',title=u"Еврокино", thumb=R('EUROKi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/uTCsQt21',title=u"Дом Кино", thumb=R('DOMKi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/SCVXMWD1',title="BBC World News", thumb=R('BBCi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/xLm8Dc4n',title="CNN International", thumb=R('CNNi.gif')))
  dir.Append(WebVideoItem('http://embed.weewza.com/dL9hrlfZ',title=u"Карусель", thumb=R('KARi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/TD6ufaBW',title="Nickelodeon", thumb=R('NICKi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/ZwPXq9q3',title="Cartoon Network", thumb=R('CARNi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/W7uKb8H3',title=u"Детский", thumb=R('DETSi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/UEOUkLCd',title="Disney", thumb=R('DISi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/jsdxZhbu',title="EuroSport 2", thumb=R('EUROS2i.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/yEzxmDhR',title="EuroSport", thumb=R('EUROSi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/9CiGK3mq',title="Extreme Sport", thumb=R('EXTi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/bxEWgR4d',title=u"Спорт 1", thumb=R('SPORi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/vo2DBxm3',title=u"АВТО Плюс", thumb=R('AVTOi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/18JzHIin',title=u"Драйв", thumb=R('DRIVEi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/NxOF9HVn',title="Viasat Sport", thumb=R('VISASi.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/9rZ28Ht4',title="VH1 Classic", thumb=R('VH1i.png')))
  dir.Append(WebVideoItem('http://embed.weewza.com/K3xkeTVd',title=u"Кухня ТВ", thumb=R('KUHTVi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/oxtHSF93',title="Shant TV", thumb=R('SHANTVi.jpg')))
  dir.Append(WebVideoItem('http://embed.weewza.com/UfxNa14y',title="AzTV", thumb=R('AZTVi.jpg')))

  # ... and then return the container
  return dir
