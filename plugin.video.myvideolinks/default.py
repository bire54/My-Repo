import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
import HTMLParser
from TheYid.common.addon import Addon
from TheYid.common.net import Net
from htmlentitydefs import name2codepoint as n2cp


try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"

addon_id = 'plugin.video.myvideolinks'
plugin = xbmcaddon.Addon(id=addon_id)

DB = os.path.join(xbmc.translatePath("special://database"), 'myvideolinks.db')
BASE_URL = 'http://www.myvideolinks.eu/'
net = Net()
addon = Addon('plugin.video.myvideolinks', sys.argv)
showAllParts = True
showPlayAll = True

if plugin.getSetting('showAllParts') == 'false':
        showAllParts = False

if plugin.getSetting('showPlayAll') == 'false':
        showPlayAll = False

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
content = addon.queries.get('content', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
listitem = addon.queries.get('listitem', None)
urlList = addon.queries.get('urlList', None)
section = addon.queries.get('section', None)
AddonPath = addon.get_path()
IconPath = AddonPath + "/icons/"
##### Queries ##########


def GetTitles(section, url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'myvideolinks get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if int(startPage)> 1:
                pageUrl = url + 'page/' + startPage + '/'
        print pageUrl
        html = net.http_GET(pageUrl).content
        CLEAN(html)

        start = int(startPage)
        end = start + int(numOfPages)

        for page in range( start, end):
                if ( page != start):
                        pageUrl = url + 'page/' + str(page) + '/'
                        html = net.http_GET(pageUrl).content
                        CLEAN(html)
                        
                match = re.compile('entry-header.+?href="(.+?)">(.+?)<', re.DOTALL).findall(html)
                for movieUrl, name in match:
                        cm  = []
                        runstring = 'XBMC.Container.Update(plugin://plugin.video.myvideolinks/?mode=Search&query=%s)' %(name.strip())
        		cm.append(('Search on myvideolinks', runstring))
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': movieUrl}, {'title':  name.strip()}, contextmenu_items= cm)
               
      
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title': '[COLOR blue][B][I]Next page...[/B][/I][/COLOR]'}, img=IconPath + 'nexts.png')        
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetLinks(section, url): # Get Links
        print 'GETLINKS FROM URL: '+url
        html = net.http_GET(str(url)).content
        CLEAN(html)
        sources = []
        listitem = GetMediaInfo(html)
        print 'LISTITEM: '+str(listitem)
        content = html
        print'CONTENT: '+str(listitem)
        r = re.search('<strong>Links.*</strong>', html)
        if r:
                content = html[r.end():]
               
        match = re.compile('href="(.+?)"').findall(content)
        listitem = GetMediaInfo(content)
        for url in match:
                host = GetDomain(url)

                if 'Unknown' in host:

                        continue
                print '*****************************' + host
                title = url.rpartition('/')
                host = host.replace('netload.in','[COLOR gold]Netload[/COLOR]')
                host = host.replace('turbobit.net','[COLOR gold]Turbobit[/COLOR]')
                host = host.replace('movreel.com','movreel.com - [COLOR red]Download/Streaming limit of 2GB a day !![/COLOR]')
                name = host
                hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
                sources.append(hosted_media)

                
        find = re.search('commentblock', html)
        if find:
                print 'in comments if'
                html = html[find.end():]
                CLEAN(html)###
                print 'MATCH IS: '+str(match)
                print len(match)
                for url in match:
                        host = GetDomain(url)
                        if 'Unknown' in host:

                                continue
        source = urlresolver.choose_source(sources)
        if source: stream_url = source.resolve()
        else: stream_url = ''
        xbmc.Player().play(stream_url)


def CLEAN(string):
    def substitute_entity(match):
        ent = match.group(3)
        if match.group(1) == "#":
            if match.group(2) == '':
                return unichr(int(ent))
            elif match.group(2) == 'x':
                return unichr(int('0x'+ent, 16))
        else:
            cp = n2cp.get(ent)
            if cp: return unichr(cp)
            else: return match.group()
    entity_re = re.compile(r'&(#?)(x?)(\d{1,5}|\w{1,8});')
    return entity_re.subn(substitute_entity, string)[0]


def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain


def GetMediaInfo(html):
        listitem = xbmcgui.ListItem()
        match = re.search('og:title" content="(.+?) \((.+?)\)', html)
        if match:
                print match.group(1) + ' : '  + match.group(2)
                listitem.setInfo('video', {'Title': match.group(1), 'Year': int(match.group(2)) } )
        return listitem

def Categories(section):  #categories

        url = BASE_URL + '/category/' + section
        html = net.http_GET(BASE_URL).content
        CLEAN(html)
        match = re.compile('<li class=.+?/category/' + section + '(.+?)".+?>(.+?)<').findall(html)
        for cat, title in match:
                url = url + cat
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url,
                                     'startPage': '1', 'numOfPages': '1'}, {'title':  title})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MainMenu():    #homescreen
        addon.add_directory({'mode': 'Categories', 'section': 'movies'},  {'title':  '[COLOR blue]Movie Categories >>[/COLOR]'}, img=IconPath + 'movies.png')
        addon.add_directory({'mode': 'GetTitles', 'section': 'ALL', 'url': BASE_URL + '/category/movies/',
                             'startPage': '1', 'numOfPages': '1'}, {'title':  '[COLOR blue]Latest Movies added >>[/COLOR]'}, img=IconPath + 'movies.png')
        addon.add_directory({'mode': 'Categories', 'section': 'tv-shows'},  {'title':  '[COLOR blue]Tv Shows list>>[/COLOR]'}, img=IconPath + 'tvs.png')
        addon.add_directory({'mode': 'GetTitles', 'section': 'ALL', 'url': BASE_URL + '/category/tv-shows/',
                             'startPage': '1', 'numOfPages': '1'}, {'title':  '[COLOR blue]Latest Tv shows added >>[/COLOR]'}, img=IconPath + 'tvs.png')
        addon.add_directory({'mode': 'GetSearchQuery'},  {'title':  '[COLOR green]Search Movies & Tv shows >>[/COLOR]'}, img=IconPath + 'searchs.png')
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  '[COLOR red]Resolver Settings[/COLOR]'}, img=IconPath + 'resolver.png')
        addon.add_directory({'mode': 'help'}, {'title':  '[COLOR pink]FOR HELP ON THIS ADDON PLEASE GOTO...[/COLOR] [COLOR gold][B][I]www.xbmchub.com[/B][/I][/COLOR]'}, img=IconPath + 'helps.png')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetSearchQuery():
	last_search = addon.load_data('search')
	if not last_search: last_search = ''
	keyboard = xbmc.Keyboard()
        keyboard.setHeading('[COLOR green]Search my video links[/COLOR]')
	keyboard.setDefault(last_search)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
                query = keyboard.getText()
                addon.save_data('search',query)
                Search(query)
	else:
                return

        
def Search(query):
        url = 'http://www.google.com/search?q=site:myvideolinks.eu  ' + query
        url = url.replace(' ', '+')
        print url
        html = net.http_GET(url).content
        CLEAN(html)
        match = re.compile('<h3 class="r"><a href="(.+?)".+?onmousedown=".+?">(.+?)</a>').findall(html)
        for url, title in match:
                title = title.replace('<b>...</b>', '').replace('<em>', '').replace('</em>', '')
                addon.add_directory({'mode': 'GetLinks', 'url': url}, {'title':  title})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


if mode == 'main': 
	MainMenu()
elif mode == 'GetTitles': 
	GetTitles(section, url, startPage, numOfPages)
elif mode == 'GetLinks':
	GetLinks(section, url)
elif mode == 'GetSearchQuery':
	GetSearchQuery()
elif mode == 'Search':
	Search(query)
elif mode == 'PlayVideo':
	PlayVideo(url, listitem)	
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
elif mode == 'Categories':
        Categories(section)
