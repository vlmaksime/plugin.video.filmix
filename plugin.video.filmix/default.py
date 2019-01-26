# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

from future.utils import iteritems
import os

from simplemedia import py2_decode
import simplemedia
import xbmc
import xbmcgui
import xbmcplugin

from resources.libs.filmix import filmix

plugin = simplemedia.RoutedPlugin()
_ = plugin.initialize_gettext()


@plugin.route('/login')
def login():
    _login = _get_keyboard_text('', _('Login'))
    if not _login:
        return

    _password = _get_keyboard_text('', _('Password'), True)
    if not _password:
        return

    dialog = xbmcgui.Dialog()
    
    try:
        login_result = api.login(_login, _password)
    except api.APIException as e:
        dialog.ok(plugin.name, e.msg)
        return
    
    user_fields = _get_user_fields(login_result)
    plugin.set_settings(user_fields)

    if user_fields['user_login']:
        dialog.ok(plugin.name, _('You have successfully logged in'))
    else:
        dialog.ok(plugin.name, _('Incorrect login or password!'))

 
@plugin.route('/logout')
def logout():

    cookie_file = _get_cookie_path()
    if os.path.exists(cookie_file):
        os.remove(cookie_file)
 
    user_fields = _get_user_fields()
    plugin.set_settings(user_fields)
 
    dialog = xbmcgui.Dialog()
    dialog.ok(plugin.name, _('You have successfully logged out'))

@plugin.route('/toogle_favorites')
def toogle_favorites():
    content_id = plugin.params.get('id')
    value = plugin.params.get('value') == '1'

    api.set_favorite(content_id, value)

    if value:
        xbmcgui.Dialog().notification(plugin.name, _('Successfully added to Favorites'), xbmcgui.NOTIFICATION_INFO)
    else:
        xbmcgui.Dialog().notification(plugin.name, _('Successfully removed from Favorites'), xbmcgui.NOTIFICATION_INFO)

    xbmc.executebuiltin(' Container.Refresh()')

@plugin.route('/toogle_watch_later')
def toogle_watch_later():
    content_id = plugin.params.get('id')
    value = plugin.params.get('value') == '1'

    api.set_watch_later(content_id, value)

    if value:
        xbmcgui.Dialog().notification(plugin.name, _('Successfully added to Watch Later'), xbmcgui.NOTIFICATION_INFO)
    else:
        xbmcgui.Dialog().notification(plugin.name, _('Successfully removed from Watch Later'), xbmcgui.NOTIFICATION_INFO)
        
        
    xbmc.executebuiltin(' Container.Refresh()')

@plugin.route('/')
def root():
    if plugin.params.action is not None:
        if plugin.params.action == 'search':
            search()
    else:
        plugin.create_directory(_root_items())


def _root_items():

    # Catalog
    for catalog_info in _get_catalogs():
        url = plugin.url_for('list_catalog', catalog=catalog_info['catalog'])
        listitem = {'label': catalog_info['label'],
                    'url': url,
                    'icon': plugin.icon,
                    'fanart': plugin.fanart,
                    'content_lookup': False,
                    }
        yield listitem

    # Popular
    url = plugin.url_for('list_catalog', catalog='popular')
    list_item = {'label': _('Popular'),
                 'url': url,
                 # 'icon': plugin.get_image('DefaultFavourites.png'),
                 'icon': plugin.icon,
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item
     
    # Top Views
    url = plugin.url_for('list_catalog', catalog='top_views')
    list_item = {'label': _('Top Views'),
                 'url': url,
                 # 'icon': plugin.get_image('DefaultFavourites.png'),
                 'icon': plugin.icon,
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item

    if plugin.get_setting('user_login'):
        # Favorites
        url = plugin.url_for('list_catalog', catalog='favorites')
        list_item = {'label': _('Favorites'),
                     'url': url,
                     'icon': plugin.get_image('DefaultFavourites.png'),
                     'fanart': plugin.fanart,
                     'content_lookup': False,
                     }
        yield list_item
    
        # Watch Later
        url = plugin.url_for('list_catalog', catalog='watch_later')
        list_item = {'label': _('Watch Later'),
                     'url': url,
                     'icon': plugin.icon,
                     'fanart': plugin.fanart,
                     'content_lookup': False,
                     }
        yield list_item
     
        # Watch History
        url = plugin.url_for('list_catalog', catalog='watch_history')
        list_item = {'label': _('Watch History'),
                     'url': url,
                     # 'icon': plugin.get_image('DefaultFavourites.png'),
                     'icon': plugin.icon,
                     'fanart': plugin.fanart,
                     'content_lookup': False,
                     }
        yield list_item
        
    # Search
    url = plugin.url_for('search_history')
    list_item = {'label': _('Search'),
                 'url': url,
                 'icon': plugin.get_image('DefaultAddonsSearch.png'),
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item


@plugin.route('/<catalog>')
def list_catalog(catalog):
    
    page = plugin.params.get('page', '1')
    page = int(page)

    per_page = plugin.get_setting('step', False)
    
    if catalog in ['watch_history', 'watch_later', 'favorites', 'popular', 'top_views']:
        params = {'page': page,
                  'per_page': per_page}
    else:
        section = _catalog_section(catalog)
        
        orderby = plugin.params.get('orderby', 'date')
        orderdir = plugin.params.get('orderdir', 'desc')
    
        params = {'page': page,
                  'section': section,
                  'orderby': orderby,
                  'orderdir': orderdir,
                  'per_page': per_page,
                  }

    try:
        if catalog == 'favorites':
            _category = _('Favorites')
            catalog_info = api.get_favorites_items(**params)
        elif catalog == 'watch_later': 
            _category = _('Watch Later')
            catalog_info = api.get_watch_later_items(**params)
        elif catalog == 'watch_history': 
            _category = _('Watch History')
            catalog_info = api.get_history_items(**params)
        elif catalog == 'popular': 
            _category = _('Popular')
            catalog_info = api.get_popular_items(**params)
        elif catalog == 'top_views': 
            _category = _('Top Views')
            catalog_info = api.get_top_views_items(**params)
        else:
            _category = _catalog_name(catalog)
            catalog_info = api.get_catalog_items(**params)
    except api.APIException as e:
        plugin.notify_error(e.msg)
        plugin.create_directory([], succeeded=False)
        return

    category_parts = [_category]
    if page > 1:
        category_parts.append('{0} {1}'.format(_('Page'), page))
    result = {'items': _catalog_items(catalog_info, catalog),
              'total_items': catalog_info['count'],
              'content': 'movies',
              'category': ' / '.join(category_parts),
              'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
              'update_listing': (page > 1),

              }
    plugin.create_directory(**result)


def _catalog_items(data, catalog):

    for item in data['items']:

        item_catalog = _section_catalog(item['section'])
        is_folder = True
        is_playable = False

        poster = item['poster']
        poster = poster.replace('thumbs/w220', 'big')
        
        url = plugin.url_for('list_content', content_id='{0}-{1}'.format(item['id'], item['alt_name']), catalog=catalog)

        if item['quality']:
            title = '{0} [{1}]'.format(item['title'], item['quality'])
        else:
            title = item['title']
        
        video_info = {'title': title,
                      'originaltitle': item['original_title'] if item['original_title'] else item['title'],
                      'sorttitle': item['title'],
                      'year': item['year'],
                      'cast': item['actors'],
                      'dateadded': '{0} {1}'.format(item['date_atom'][0:10], item['date_atom'][11:19]),
                      'mediatype': 'movie' if item['section'] in [0, 14] else 'tvshow',
                      }

        listitem = {'label': video_info['title'],
                    'info': {'video': video_info,
                             },
                    'art': {'poster': poster},
                    'content_lookup': False,
                    'is_folder': is_folder,
                    'is_playable': is_playable,
                    'url': url,
                    'fanart':  plugin.fanart,
                    'thumb':  poster,
                    'context_menu': _get_context_menu(item),
                    }
        
        yield listitem

    pages = data.get('pages', {})
    if pages.get('prev') is not None:
        url = plugin.url_for('list_catalog', catalog=catalog, **pages['prev'])
        item_info = {'label': _('Previous page...'),
                     'url':   url}
        yield item_info
 
    if pages.get('next') is not None:
        url = plugin.url_for('list_catalog', catalog=catalog, **pages['next'])
        item_info = {'label': _('Next page...'),
                     'url':   url}
        yield item_info


@plugin.route('/<catalog>/<content_id>')
def list_content(catalog, content_id):
    content_params = _get_content_params(content_id)
    
    try:
        content_info = api.get_movie_info(**content_params)
    except api.APIException as e:
        plugin.notify_error(e.msg)
        plugin.create_directory([], succeeded=False)
        return

    if content_info['section'] in [0, 14]:
        result = {'items': _list_movie_files(content_info),
                  'content': 'movies',
                  'category': content_info['title'],
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  }
    else:
        result = {'items': _list_serial_seasons(content_info),
                  'content': 'seasons',
                  'category': content_info['title'],
                  'sort_methods': xbmcplugin.SORT_METHOD_LABEL,
                  }

    plugin.create_directory(**result)


def _list_movie_files(item):

    listitem = _get_listitem(item)

    del listitem['info']['video']['title']

    listitem['is_folder'] = False
    listitem['is_playable'] = True

    player_links = _get_player_links(item)

    u_params = {'content_id': '{0}-{1}'.format(item['id'], item['alt_name']),
                'catalog': _section_catalog(item['section'])
                }
    
    for link in player_links:
        url = plugin.url_for('play_video', t=link['translation'], **u_params)
        listitem['url'] = url
        listitem['label'] = '{0} ({1})'.format(item['title'], link['translation'])

        yield listitem


def _list_serial_seasons(item):

    listitem = _get_listitem(item)

    listitem['is_folder'] = True
    listitem['is_playable'] = False
    listitem['info']['video']['mediatype'] = 'season'

    player_links = _get_player_links(item)

    if isinstance(player_links, dict):
        for season, season_translations in iteritems(player_links):

            listitem['info']['video']['season'] = int(season)
            listitem['info']['video']['sortseason'] = int(season)
            
            u_params = {'content_id': '{0}-{1}'.format(item['id'], item['alt_name']),
                        'catalog': _section_catalog(item['section']),
                        's': season,
                        }

            for translation, translation_info in iteritems(season_translations):
                url = plugin.url_for('list_season_episodes', t=translation, **u_params)
                listitem['url'] = url
                listitem['label'] = '{0} {1} ({2})'.format(_('Season'), season, translation)
        
                yield listitem
    else:
        listitem['info']['video']['season'] = 1
        listitem['info']['video']['sortseason'] = 1
        
        u_params = {'content_id': '{0}-{1}'.format(item['id'], item['alt_name']),
                    'catalog': _section_catalog(item['section']),
                    }

        for season_translations in player_links:
            for translation, translation_info in iteritems(season_translations):
                url = plugin.url_for('list_season_episodes', t=translation, **u_params)
                listitem['url'] = url
                listitem['label'] = translation
        
                yield listitem
 
    
@plugin.route('/<catalog>/<content_id>/episodes')
def list_season_episodes(catalog, content_id):
    content_params = _get_content_params(content_id)
    
    try:
        serial_info = api.get_movie_info(**content_params)
    except api.APIException as e:
        plugin.notify_error(e.msg)
        plugin.create_directory([], succeeded=False)
        return

    season = plugin.params.s
    translation = plugin.params.get('t')

    result = {'items': _season_episodes_items(serial_info, season, translation),
              'content': 'episodes',
              'category': ' / '.join([serial_info['title'], '{0} {1}'.format(_('Season'), season)]),
              'sort_methods': xbmcplugin.SORT_METHOD_EPISODE,
              }
    
    plugin.create_directory(**result)


def _season_episodes_items(item, season=None, translation=None):

    listitem = _get_listitem(item)

    listitem['is_folder'] = False
    listitem['is_playable'] = True

    listitem['info']['video']['season'] = int(season) if season is not None else 1
    listitem['info']['video']['sortseason'] = int(season) if season is not None else 1
    listitem['info']['video']['mediatype'] = 'episode'
    
    season_translation = _get_season_translation(item, season, translation)

    u_params = {'content_id': '{0}-{1}'.format(item['id'], item['alt_name']),
                'catalog': _section_catalog(item['section']),
                't': translation,
                }
    if season is not None:
        u_params['s'] = season
    
    for episode, link in iteritems(season_translation):

        listitem['info']['video']['episode'] = int(episode)
        listitem['info']['video']['sortepisode'] = int(episode) 
    
        url = plugin.url_for('play_video', e=episode, **u_params)
        listitem['url'] = url
        listitem['label'] = '{0} {1}'.format(_('Episode'), episode)

        listitem['info']['video']['title'] = listitem['label']

        yield listitem

    
@plugin.route('/<catalog>/<content_id>/play')
def play_video(catalog, content_id):

    content_params = _get_content_params(content_id)

    try:
        content_info = api.get_movie_info(**content_params)
    except api.APIException as e:
        plugin.notify_error(e.msg)
        plugin.resolve_url({}, False)
        return

    is_strm = plugin.params.get('strm') == '1' \
               and plugin.kodi_major_version() >= '18'

    translation = plugin.params.get('t')
    season = plugin.params.get('s')
    episode = plugin.params.get('e')

    if is_strm:
        listitem = {}
    else:
        listitem = _get_listitem(content_info)

        listitem['is_folder'] = False
        listitem['is_playable'] = True
    
        if content_info['section'] in [0, 14]:
            listitem['info']['video']['mediatype'] = 'movie'
        else:
            listitem['info']['video']['season'] = int(season) if season is not None else 1
            listitem['info']['video']['episode'] = int(episode)
            listitem['info']['video']['mediatype'] = 'episode'

            listitem['label'] = '{0} {1}'.format(_('Episode'), episode)
            listitem['info']['video']['title'] = listitem['label']
    
    if content_info['section'] in [0, 14]:
        listitem['path'] = _get_movie_link(content_info, translation)
    else:
        listitem['path'] = _get_episode_link(content_info, season, episode, translation)
            
    plugin.resolve_url(listitem)


def  _get_catalogs():
    list = [{'catalog': 'movies', 'label': _('Movies'), 'section': 0},
            {'catalog': 'serials', 'label': _('TV Series'), 'section': 7},
            {'catalog': 'multfilms', 'label': _('Cartoons'), 'section': 14},
            {'catalog': 'multserials', 'label': _('Cartoon Series'), 'section': 93},
            ]
    
    return list


def _get_season_translation(item, season, translation):
    player_links = _get_player_links(item)

    if isinstance(player_links, dict):
        season_translations = player_links.get(season)
    
        if translation is not None:
            season_translation = season_translations.get(translation)
        else:
            season_translation = None
        
        if season_translation is None:
            for key, translation_info in iteritems(season_translations):
                season_translation = translation_info
                break
    else:
        season_translation = None
        for season_translations in player_links:
            for key, translation_info in iteritems(season_translations):
                if key == translation \
                    or translation is None:
                    season_translation = translation_info
                    break
                elif season_translation is None:
                    season_translation = translation_info
    
    return season_translation


def _catalog_name(catalog):
    for item in _get_catalogs():
        if item['catalog'] == catalog:
            return item['label']


def _section_catalog(section):
    for item in _get_catalogs():
        if item['section'] == section:
            return item['catalog']


def _catalog_section(catalog):
    for item in _get_catalogs():
        if item['catalog'] == catalog:
            return item['section']


def _get_content_params(content_id):
    sep = content_id.find('-')
    
    result = {'newsid': content_id[:sep],
              'alt_name': content_id[sep + 1:],
              }

    return result


def _get_player_links(item):
    link_source = 'movie' if item['section']  in [0, 14] else 'playlist'
    return item['player_links'][link_source]


def _get_movie_link(item, translation=None):
    player_links = _get_player_links(item)
    
    url = player_links[0]['link']

    if len(player_links) > 1 \
      and translation is not None:
        for link in player_links:
            if link['translation'] == translation:
                url = link['link']
                break
            
    url = api.decode_link(url)
    
    sub_a = url.find('[')
    sub_b = url.find(']')
    qualities = url[sub_a + 1:sub_b].split(',')

    video_quality = plugin.get_setting('video_quality') + 1
    quality_list = _available_qualities()
    
    path = None
    for i, q in enumerate(quality_list):
        if (path is None or video_quality >= i) \
         and q in qualities:
            path = url.replace(url[sub_a:sub_b + 1], q)

    return path


def _get_episode_link(item, season, episode, translation=None):
    season_translation = _get_season_translation(item, season, translation)

    episode_info = season_translation[episode]
            
    url = api.decode_link(episode_info['link'])
    qualities = episode_info['qualities']

    video_quality = plugin.get_setting('video_quality') + 1
    quality_list = _available_qualities()
    
    path = None
    for i, q in enumerate(quality_list):
        if (path is None or video_quality >= i) \
         and int(q) in qualities:
            path = url % q

    return path


def _available_qualities():
    _user_data()

    if plugin.get_setting('is_pro_plus'):
        return ['360', '480', '720', '1080', '1440', '2160']
    else:
        return ['360', '480', '720']
        

def _get_listitem(item):

    poster = item['poster']
    poster = poster.replace('thumbs/w220', 'big')
    
    ratings = _get_ratings(item)

    rating = 0
    for _rating in ratings:
        if _rating['defaultt']:
            rating = _rating['rating']
            break

    video_info = {'year': item['year'],
                  'cast': item['actors'],
                  'director': item['directors'],
                  'duration': item['duration'] * 60,
                  'plot': plugin.remove_html(item['short_story']),
                  'dateadded': '{0} {1}'.format(item['date_atom'][0:10], item['date_atom'][11:19]),
                  'country': item['countries'],
                  'genre': item['categories'],
                  'rating': rating,
                  }

    if item['section'] in [0, 14]:
        video_info.update({'mediatype': 'movie',
                           'title': item['title'],
                           'originaltitle': item['original_title'] if item['original_title'] else item['title'],
                           'sorttitle': item['title'],
      #                  'premiered': item['release_date'],
                         })
    else:
        video_info.update({  # 'mediatype': 'episode',
                           'tvshowtitle': item['title'],
                           })

    listitem = {'label': item['title'],
                'info': {'video': video_info,
                         },
                'art': {'poster': poster},
                'content_lookup': False,
                'fanart':  plugin.fanart,
                'thumb':  poster,
                'ratings': ratings,
                }
    return listitem    


@plugin.route('/search/history')
def search_history():
 
    with plugin.get_storage('__history__.pcl') as storage:
        history = storage.get('history', [])
 
        if len(history) > plugin.get_setting('history_length'):
            history[plugin.history_length - len(history):] = []
            storage['history'] = history
 
    listing = []
    listing.append({'label': _('New Search...'),
                    'url': plugin.url_for('search'),
                    'icon': plugin.get_image('DefaultAddonsSearch.png'),
                    'is_folder': False,
                    'is_playable': False,
                    'fanart': plugin.fanart})
 
    for item in history:
        listing.append({'label': item['keyword'],
                        'url': plugin.url_for('search', keyword=item['keyword']),
                        'icon': plugin.icon,
                        'is_folder': True,
                        'is_playable': False,
                        'fanart': plugin.fanart})
 
    plugin.create_directory(listing, content='files', category=_('Search'))
 
 
@plugin.route('/search')
def search():
 
    keyword = plugin.params.keyword or ''
    usearch = (plugin.params.usearch == 'True')

    page = plugin.params.get('page', '1')
    page = int(page)
 
    new_search = (keyword == '')
 
    if not keyword:
        kbd = xbmc.Keyboard('', _('Search'))
        kbd.doModal()
        if kbd.isConfirmed():
            keyword = kbd.getText()
 
    if keyword and new_search and not usearch:
        with plugin.get_storage('__history__.pcl') as storage:
            history = storage.get('history', [])
            history.insert(0, {'keyword': keyword})
            if len(history) > plugin.get_setting('history_length'):
                history.pop(-1)
            storage['history'] = history

        plugin.create_directory([], succeeded=False)
 
        url = plugin.url_for('search', keyword=py2_decode(keyword))
        xbmc.executebuiltin('Container.Update("%s")' % url)
 
    elif keyword:
        try:
            catalog_info = api.get_search_catalog(keyword, page)
        except api.APIException as e:
            plugin.notify_error(e.msg)
            plugin.create_directory([], succeeded=False)
            return
    
        result = {'items': _catalog_items(catalog_info, 'search'),
                  'total_items': catalog_info['count'],
                  'content': 'movies',
                  'category': ' / '.join([_('Search'), keyword]),
    #                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  'update_listing': (page > 1),
    
                  }
        plugin.create_directory(**result)


def _get_keyboard_text(line='', heading='', hidden=False):            
    kbd = xbmc.Keyboard(line, heading, hidden)
    kbd.doModal()
    if kbd.isConfirmed():
        return kbd.getText()
     
     
def _get_user_fields(user_info=None):
    user_info = user_info or {}

    fields = {'user_login': user_info.get('login') or '',
              'user_name': user_info.get('display_name') or '',
              'is_pro': user_info.get('is_pro') or False,
              'is_pro_plus': user_info.get('is_pro_plus') or False,
              'pro_date': user_info.get('pro_date') or '',
              'X-FX-Token': user_info.get('X-FX-Token') or '',
              }
    return fields


def _get_cookie_path():
    return os.path.join(plugin.profile_dir, 'filmix.cookies')
    

def _api():
    cookie_file = _get_cookie_path()

    headers = {'X-FX-Token': plugin.get_setting('X-FX-Token'),
               }

    api = filmix(headers, cookie_file)
    
    return api


def _user_data():
    user_data = api.user_data()
    user_fields = _get_user_fields(user_data)
    plugin.set_settings(user_fields)
    
    return user_data
    

def _get_rating_source():
    rating_source = plugin.get_setting('video_rating')
    if rating_source == 0:
        source = 'imdb'
    elif rating_source == 1:
        source = 'kinopoisk'
    return source


def _rating_sources():
    yield {'rating_source': 'kinopoisk',
           'field': 'kp',
           }
    yield {'rating_source': 'imdb',
           'field': 'imdb',
           }

 
def _get_ratings(item):
    default_source = _get_rating_source()
    items = []
    for rating in _rating_sources():
        rating_item = _make_rating(item, **rating)
        rating_item['defaultt'] = (rating_item['type'] == default_source)
        items.append(rating_item)

    return items

 
def _make_rating(item, rating_source, field):
    rating_field = '_'.join([field, 'rating'])
    rating = item.get(rating_field, '0')
    if rating \
      and rating != '-':
        rating = float(rating)
    else:
        rating = 0
 
    votes_field = '_'.join([field, 'votes'])
    votes = item.get(votes_field, '0')
    if votes \
      and votes != '-':
        votes = int(votes)
    else:
        votes = 0
 
    return {'type': rating_source,
            'rating': rating,
            'votes': votes,
            'defaultt': False,
            }
 
def _get_context_menu(item):
    context_menu = []
    
    if plugin.get_setting('user_login'):
        
        url = plugin.url_for('toogle_favorites', id=item['id'], value=(0 if item['favorited'] else 1))
        if item['favorited']:
            context_menu.append((_('Remove from Favorites'),'RunPlugin({0})'.format(url)))
        else:
            context_menu.append((_('Add to Favorites'),'RunPlugin({0})'.format(url)))
            
        url = plugin.url_for('toogle_watch_later', id=item['id'], value=(0 if item['watch_later'] else 1))
        if item['watch_later']:
            context_menu.append((_('Remove from Watch Later'),'RunPlugin({0})'.format(url)))
        else:
            context_menu.append((_('Add to Watch Later'),'RunPlugin({0})'.format(url)))
        
    return context_menu

 
def _use_atl_names():
    return plugin.params.get('atl', '').lower() == 'true' \
             or plugin.get_setting('use_atl_names')
    

if __name__ == '__main__':
    api = _api()
    plugin.run()
