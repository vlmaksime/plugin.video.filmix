# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import os

import simplemedia
import xbmc
import xbmcgui
import xbmcplugin
from future.utils import iteritems
from resources.libs import Filmix, FilmixError
from simplemedia import py2_decode

plugin = simplemedia.RoutedPlugin()
_ = plugin.initialize_gettext()


@plugin.route('/login')
def login():
    try:
        api = Filmix()
        token_result = api.token_request()
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e, True)
    else:
        api.update_dev_token(token_result['code'])
        plugin.set_setting('user_dev_token', token_result['code'])

        code = token_result['user_code']

        main_link = 'filmix.co/consoles'
        mirror_link = 'filmix.co/consoles'

        progress = plugin.dialog_progress_create(_('Login by Code'),
                                                 _('Connection code: [B]{0}[/B]').format(code),
                                                 _('Enter code on the page [B]{0}[/B] ([B]{1}[/B] for residents of the RF)').format(main_link, mirror_link),
                                                 _('or in the site menu [B]\'Profile\' -> \'Consoles\'[/B]'))

        wait_sec = 300
        step_sec = 2
        pass_sec = 0
        check_sec = 20

        user_fields = api.get_user_fields()
        while pass_sec < wait_sec:
            if progress.iscanceled():
                return

            xbmc.sleep(step_sec * 1000)
            pass_sec += step_sec

            plugin.dialog_progress_update(progress, int(100 * pass_sec / wait_sec))

            if (pass_sec % check_sec) == 0:
                try:
                    user_data = api.user_data()
                except (FilmixError, simplemedia.WebClientError) as e:
                    plugin.notify_error(e)
                else:
                    user_fields = api.get_user_fields(user_data)
                    if user_fields['user_login']:
                        break

        progress.close()

        plugin.set_settings(user_fields)

        if user_fields['user_login']:
            plugin.dialog_ok(_('You have successfully logged in'))
        else:
            plugin.dialog_ok(_('Login failure! Please, try later'))


@plugin.route('/select_videoserver')
def select_videoserver():
    api = Filmix()
    try:
        user_data = api.user_data()
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e)
    else:
        keys = []
        titles = []
        for key, val in iteritems(user_data.get('available_servers')):
            titles.append(val)
            keys.append(key)

        videoserver = user_data.get('videoserver') or 'AUTO'

        if titles:
            if plugin.kodi_major_version() >= '17':
                preselect = keys.index(videoserver)
                selected = xbmcgui.Dialog().select(_('Select video server'), titles, preselect=preselect)
            else:
                selected = xbmcgui.Dialog().select(_('Select video server'), titles)

            if selected is not None \
                    and keys[selected] != videoserver:
                try:
                    result = api.set_videoserver(keys[selected])
                except (FilmixError, simplemedia.WebClientError) as e:
                    plugin.notify_error(e)
                else:
                    if result['status'] == 'ok' \
                            and videoserver != result['server']:
                        plugin.set_setting('videoserver', user_data['available_servers'].get(result['server']))
                        xbmcgui.Dialog().notification(plugin.name, _('Video server successfully changed'), xbmcgui.NOTIFICATION_INFO)


@plugin.route('/check_device')
def check_device():
    Filmix().check_device()


@plugin.route('/toogle_favorites')
def toogle_favorites():
    content_id = plugin.params.get('id')
    value = plugin.params.get('value') == '1'

    try:
        api = Filmix()
        api.set_favorite(content_id, value)
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e, True)
    else:
        if value:
            xbmcgui.Dialog().notification(plugin.name, _('Successfully added to Favorites'), xbmcgui.NOTIFICATION_INFO)
        else:
            xbmcgui.Dialog().notification(plugin.name, _('Successfully removed from Favorites'), xbmcgui.NOTIFICATION_INFO)

        xbmc.executebuiltin(' Container.Refresh()')


@plugin.route('/toogle_watch_later')
def toogle_watch_later():
    content_id = plugin.params.get('id')
    value = plugin.params.get('value') == '1'

    try:
        api = Filmix()
        api.set_watch_later(content_id, value)
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e, True)
    else:
        if value:
            xbmcgui.Dialog().notification(plugin.name, _('Successfully added to Watch Later'), xbmcgui.NOTIFICATION_INFO)
        else:
            xbmcgui.Dialog().notification(plugin.name, _('Successfully removed from Watch Later'), xbmcgui.NOTIFICATION_INFO)

        xbmc.executebuiltin(' Container.Refresh()')


@plugin.route('/')
def root():
    plugin.create_directory(_root_items(), content='', category=plugin.name)


def _root_items():
    # Catalog
    for catalog_info in _get_catalogs():
        url = plugin.url_for('list_catalog', catalog=catalog_info['catalog'])
        listitem = {'label': catalog_info['label'],
                    'url': url,
                    'icon': catalog_info['icon'],
                    'fanart': plugin.fanart,
                    'content_lookup': False,
                    }
        yield listitem

    movie_icon = plugin.get_image('DefaultMovies.png')

    # Popular
    url = plugin.url_for('list_catalog', catalog='popular')
    list_item = {'label': _('Popular'),
                 'url': url,
                 'icon': movie_icon,
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item

    # Top Views
    url = plugin.url_for('list_catalog', catalog='top_views')
    list_item = {'label': _('Top Views'),
                 'url': url,
                 'icon': movie_icon,
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
                     'icon': plugin.get_image('DefaultFavourites.png'),
                     'fanart': plugin.fanart,
                     'content_lookup': False,
                     }
        yield list_item

        # Watch History
        url = plugin.url_for('list_catalog', catalog='watch_history')
        list_item = {'label': _('Watch History'),
                     'url': url,
                     'icon': movie_icon,
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


@plugin.route('/<catalog>', 'list_catalog_old')
@plugin.route('/<catalog>/')
def list_catalog(catalog):
    page = plugin.params.get('page', '1')
    page = int(page)

    per_page = plugin.get_setting('step', False)

    if catalog in ['watch_history', 'watch_later', 'favorites', 'popular', 'top_views']:
        use_filters = False
        params = {'page': page,
                  'per_page': per_page}
    else:
        use_filters = plugin.get_setting('use_filters')
        section = _catalog_section(catalog)

        orderby = plugin.params.get('orderby', 'date')
        orderdir = plugin.params.get('orderdir', 'desc')
        filters = plugin.params.get('filters', '')

        params = {'page': page,
                  'section': section,
                  'orderby': orderby,
                  'orderdir': orderdir,
                  'per_page': per_page,
                  'filters': filters,
                  }

    try:
        api = Filmix()
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
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e)
        plugin.create_directory([], succeeded=False)
    else:
        wm_params = {'catalog': catalog,
                     'wm_link': 1,
                     }
        wm_params.update(plugin.params)
        if wm_params.get('page') is not None:
            del wm_params['page']

        wm_properties = {'wm_link': plugin.url_for('list_catalog', **wm_params),
                         'wm_addon': plugin.id,
                         'wm_label': _category,
                         }

        category_parts = [_category]
        if page > 1:
            category_parts.append('{0} {1}'.format(_('Page'), page))
        result = {'items': _catalog_items(catalog_info, catalog, use_filters, wm_properties),
                  'total_items': catalog_info['count'],
                  'content': 'movies',
                  'category': ' / '.join(category_parts),
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  'update_listing': (page > 1),

                  }
        plugin.create_directory(**result)


def _catalog_items(data, catalog, use_filters=False, wm_properties=None):
    wm_link = (plugin.params.get('wm_link') == '1')

    if not wm_link \
            and use_filters:
        used_filters = _get_filters()
        for used_filter in used_filters:
            yield _make_filter_item(catalog, used_filter['t'])

    properties = {}
    properties.update(wm_properties or {})

    for item in data['items']:

        if not isinstance(item, dict):
            continue

        is_folder = True
        is_playable = False

        poster = item['poster']
        poster = poster.replace('thumbs/w220', 'big')

        url = plugin.url_for('list_content', content_name='{0}-{1}'.format(item['id'], item['alt_name']), catalog=catalog)

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
                      'mediatype': 'movie' if _is_movie(item) else 'tvshow',
                      }

        listitem = {'label': video_info['title'],
                    'info': {'video': video_info,
                             },
                    'art': {'poster': poster},
                    'content_lookup': False,
                    'is_folder': is_folder,
                    'is_playable': is_playable,
                    'url': url,
                    'fanart': plugin.fanart,
                    'thumb': poster,
                    'context_menu': _get_context_menu(item),
                    'properties': properties,
                    }

        yield listitem

    if not wm_link:
        pages = data.get('pages', {})
        if pages.get('prev') is not None:
            url = plugin.url_for('list_catalog', catalog=catalog, **pages['prev'])
            item_info = {'label': _('Previous page...'),
                         'url': url}
            yield item_info

        if pages.get('next') is not None:
            url = plugin.url_for('list_catalog', catalog=catalog, **pages['next'])
            item_info = {'label': _('Next page...'),
                         'url': url}
            yield item_info


@plugin.route('/select_filter')
def select_filter():
    catalog = plugin.params.get('catalog')
    filter_id = plugin.params.get('filter_id')

    filter_title = _get_filter_title(filter_id)
    values_list = _get_filter_values(filter_id)
    #    values_list =  sorted(values_list, key=values_list.get)

    filter_values = _get_catalog_filters()

    keys = []
    titles = []
    preselected = []

    for filter_item in values_list:
        titles.append(filter_item['val'])
        keys.append(filter_item['id'])
        if filter_item['id'] in filter_values:
            preselected.append(keys.index(filter_item['id']))
            filter_values.remove(filter_item['id'])

    if plugin.kodi_major_version() >= '17':
        selected = xbmcgui.Dialog().multiselect(filter_title, titles, preselect=preselected)
    else:
        selected = xbmcgui.Dialog().multiselect(filter_title, titles)

    if selected is not None:
        for _index in selected:
            filter_values.append(keys[_index])

        params = {}
        if filter_values:
            params['filters'] = '-'.join(filter_values)

        url = plugin.url_for('list_catalog', catalog=catalog, **params)
        xbmc.executebuiltin('Container.Update("%s")' % url)


@plugin.route('/<catalog>/<content_name>', 'list_content_old')
@plugin.route('/<catalog>/<content_name>/')
def list_content(catalog, content_name):
    if catalog == 'openmeta':
        openmeta_search(content_name)
    else:
        content = _get_content_params(content_name)

        try:
            api = Filmix()
            content_info = api.get_movie_info(content['id'], content['alt_name'])
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e)
            plugin.create_directory([], succeeded=False)
        else:

            if _is_movie(content_info):
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

    use_atl_names = _use_atl_names()

    listitem['is_folder'] = False
    listitem['is_playable'] = True

    player_links = _get_player_links(item)

    u_params = {'content_name': '{0}-{1}'.format(item['id'], item['alt_name']),
                'catalog': _section_catalog(item['section'])
                }

    if use_atl_names:
        atl_name_parts = []
        if item.get('original_title', ''):
            movie_title = item['original_title']
        else:
            movie_title = item['title']
        atl_name_parts.append(movie_title)

        atl_name_parts.append('(%d)' % (item['year']))

        title = ' '.join(atl_name_parts)
    else:
        title = item['title']

    for link in player_links:
        url = plugin.url_for('play_video', t=link['translation'], **u_params)
        listitem['url'] = url
        if use_atl_names:
            listitem['label'] = '{0} [{1}]'.format(title, link['translation'])
        else:
            listitem['label'] = '{0} ({1})'.format(title, link['translation'])

        yield listitem


def _list_serial_seasons(item):
    listitem = _get_listitem(item)

    listitem['is_folder'] = True
    listitem['is_playable'] = False
    listitem['info']['video']['mediatype'] = 'season'

    player_links = _get_player_links(item)

    use_atl_names = _use_atl_names()
    ext_params = {}
    if use_atl_names:
        ext_params['atl'] = use_atl_names

    if isinstance(player_links, dict):
        for season, season_translations in iteritems(player_links):

            listitem['info']['video']['season'] = int(season)
            listitem['info']['video']['sortseason'] = int(season)

            u_params = {'content_name': '{0}-{1}'.format(item['id'], item['alt_name']),
                        'catalog': _section_catalog(item['section']),
                        's': season,
                        }
            u_params.update(ext_params)

            for translation_item in iteritems(season_translations):
                translation = translation_item[0]

                url = plugin.url_for('list_season_episodes', t=translation, **u_params)
                listitem['url'] = url
                listitem['label'] = '{0} {1} ({2})'.format(_('Season'), season, translation)

                yield listitem
    else:
        listitem['info']['video']['season'] = 1
        listitem['info']['video']['sortseason'] = 1

        u_params = {'content_name': '{0}-{1}'.format(item['id'], item['alt_name']),
                    'catalog': _section_catalog(item['section']),
                    }
        u_params.update(ext_params)

        for season_translations in player_links:
            for translation_item in iteritems(season_translations):
                translation = translation_item[0]
                url = plugin.url_for('list_season_episodes', t=translation, **u_params)
                listitem['url'] = url
                listitem['label'] = translation

                yield listitem


@plugin.route('/<catalog>/<content_name>/episodes', 'list_season_episodes_old')
@plugin.route('/<catalog>/<content_name>/episodes/')
def list_season_episodes(catalog, content_name):
    content = _get_content_params(content_name)

    try:
        api = Filmix()
        serial_info = api.get_movie_info(content['id'], content['alt_name'])
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e)
        plugin.create_directory([], succeeded=False)
    else:
        season = plugin.params.s
        translation = plugin.params.get('t')

        use_atl_names = _use_atl_names()
        if use_atl_names:
            sort_methods = xbmcplugin.SORT_METHOD_TITLE
        else:
            sort_methods = xbmcplugin.SORT_METHOD_EPISODE

        result = {'items': _season_episodes_items(serial_info, season, translation),
                  'content': 'episodes',
                  'category': ' / '.join([serial_info['title'], '{0} {1}'.format(_('Season'), season)]),
                  'sort_methods': sort_methods,
                  }

        plugin.create_directory(**result)


def _season_episodes_items(item, season=None, translation=None):
    listitem = _get_listitem(item)

    use_atl_names = _use_atl_names()

    listitem['is_folder'] = False
    listitem['is_playable'] = True

    int_season = max(1, int(season or '1'))

    listitem['info']['video']['season'] = int_season
    listitem['info']['video']['sortseason'] = int_season
    listitem['info']['video']['mediatype'] = 'episode'

    season_translation = _get_season_translation(item, season, translation)

    u_params = {'content_name': '{0}-{1}'.format(item['id'], item['alt_name']),
                'catalog': _section_catalog(item['section']),
                }
    if translation is not None:
        u_params['t'] = translation

    if season is not None:
        u_params['s'] = season

    if use_atl_names:
        u_params['strm'] = 1

    if season_translation is not None:
        if isinstance(season_translation, list):
            for episode, episode_info in enumerate(season_translation):
                _add_episode_info(listitem, episode + 1, int_season, item, use_atl_names, u_params)

                yield listitem
        else:
            for episode_item in iteritems(season_translation):
                episode = episode_item[0]
                _add_episode_info(listitem, episode, int_season, item, use_atl_names, u_params)

                yield listitem


@plugin.route('/<catalog>/<content_name>/play', 'play_video_old')
@plugin.route('/<catalog>/<content_name>/play/')
def play_video(catalog, content_name):
    content = _get_content_params(content_name)

    try:
        api = Filmix()
        content_info = api.get_movie_info(content['id'], content['alt_name'])
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e)
        plugin.resolve_url({}, False)
    else:

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

            if _is_movie(content_info):
                listitem['info']['video']['mediatype'] = 'movie'
            else:
                int_season = max(1, int(season or '1'))
                listitem['info']['video']['season'] = int_season
                listitem['info']['video']['episode'] = int(episode)
                listitem['info']['video']['mediatype'] = 'episode'

                listitem['label'] = '{0} {1}'.format(_('Episode'), episode)
                listitem['info']['video']['title'] = listitem['label']

        if _is_movie(content_info):
            listitem['path'] = _get_movie_link(content_info, translation)
        else:
            listitem['path'] = _get_episode_link(content_info, season, episode, translation)

        data = {'post_id': content['id'],
                'translation': translation,
                'season': season,
                'episode': episode,
                }
        plugin.send_notification('OnPlay', data)

        plugin.resolve_url(listitem)


@plugin.route('/<catalog>/<content_name>/trailer')
def play_trailer(catalog, content_name):
    content = _get_content_params(content_name)

    try:
        api = Filmix()
        content_info = api.get_movie_info(content['id'], content['alt_name'])
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e)
        plugin.resolve_url({}, False)
    else:

        listitem = {'path': _get_trailer_link(content_info),
                    }

        plugin.resolve_url(listitem)


def _get_catalogs():
    movie_icon = plugin.get_image('DefaultMovies.png')
    tvshow_icon = plugin.get_image('DefaultTVShows.png')

    catalogs = [{'catalog': 'movies', 'label': _('Movies'), 'section': 0, 'icon': movie_icon},
                {'catalog': 'serials', 'label': _('TV Series'), 'section': 7, 'icon': tvshow_icon},
                {'catalog': 'multfilms', 'label': _('Cartoons'), 'section': 14, 'icon': movie_icon},
                {'catalog': 'multserials', 'label': _('Cartoon Series'), 'section': 93, 'icon': tvshow_icon},
                ]

    return catalogs


def _get_season_translation(item, season, translation):
    player_links = _get_player_links(item)

    if isinstance(player_links, dict):
        link_season = season or '-1'
        season_translations = player_links.get(link_season)

        if season_translations is not None:
            season_translation = season_translations.get(translation)
        else:
            season_translation = None

        if season_translation is None \
                and season_translations is not None:
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


def _get_content_params(content_name):
    sep = content_name.find('-')

    result = {'id': content_name[:sep],
              'alt_name': content_name[sep + 1:],
              }

    return result


def _get_player_links(item):
    link_source = 'movie' if _is_movie(item) else 'playlist'
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

    api = Filmix()
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

    if season_translation is None:
        return None

    if isinstance(season_translation, list):
        episode_info = season_translation[int(episode) - 1]
    else:
        episode_info = season_translation[episode]

    api = Filmix()
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


def _get_trailer_link(item):
    player_links = item['player_links'].get('trailer')

    if player_links is None \
            or len(player_links) == 0:
        return ''

    url = player_links[0]['link']

    api = Filmix()
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


def _available_qualities():
    if plugin.get_setting('is_pro_plus'):
        return ['360', '480', '720', '1080', '1440', '2160']
    elif plugin.get_setting('user_login'):
        return ['360', '480', '720']
    else:
        return ['360', '480']


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

    if _is_movie(item):
        video_info.update({'mediatype': 'movie',
                           'title': item['title'],
                           'originaltitle': item['original_title'] if item['original_title'] else item['title'],
                           'sorttitle': item['title'],
                           # 'premiered': item['release_date'],
                           })
    else:
        video_info.update({  # 'mediatype': 'episode',
                           'tvshowtitle': item['title'],
                           })

    if item['player_links'].get('trailer') is not None:
        trailer_params = {'content_name': '{0}-{1}'.format(item['id'], item['alt_name']),
                          'catalog': _section_catalog(item['section']),
                          }
        video_info['trailer'] = plugin.url_for('play_trailer', **trailer_params)

    listitem = {'label': item['title'],
                'info': {'video': video_info,
                         },
                'art': {'poster': poster},
                'content_lookup': False,
                'fanart': plugin.fanart,
                'thumb': poster,
                'ratings': ratings,
                }
    return listitem


@plugin.route('/search/history/')
def search_history():
    result = {'items': plugin.search_history_items(),
              'content': '',
              'category': ' / '.join([plugin.name, _('Search')]),
              'sort_methods': xbmcplugin.SORT_METHOD_NONE,
              }

    plugin.create_directory(**result)


@plugin.route('/search/remove/<int:index>')
def search_remove(index):
    plugin.search_history_remove(index)


@plugin.route('/search/clear')
def search_clear():
    plugin.search_history_clear()


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
            api = Filmix()
            catalog_info = api.get_search_catalog(keyword, page)
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e)
            plugin.create_directory([], succeeded=False)
        else:

            result = {'items': _catalog_items(catalog_info, 'search'),
                      'total_items': catalog_info['count'],
                      'content': 'movies',
                      'category': ' / '.join([_('Search'), keyword]),
                      'sort_methods': xbmcplugin.SORT_METHOD_NONE,
                      'update_listing': (page > 1),

                      }
            plugin.create_directory(**result)


def _get_filter_prefix(filter_id):
    filters = _get_filters()
    for _filter in filters:
        if _filter['t'] == filter_id:
            return _filter['p']


def _get_filter_values(filter_id):
    storage = plugin.get_mem_storage()
    filters = storage.get('filters', {})
    if filters.get(filter_id) is not None:
        return filters[filter_id]

    try:
        api = Filmix()
        result = api.get_filter('cat', filter_id)
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e)
        filter_values = []
    else:
        prefix = _get_filter_prefix(filter_id)
        filter_values = []
        start_index = 0 if filter_id in ['years'] else 1
        for key, val in iteritems(result):
            filter_values.append({'id': prefix + key[start_index:],
                                  'val': val,
                                  })

        filter_values.sort(key=_sort_by_val)

        filters[filter_id] = filter_values
        storage['filters'] = filters

    return filter_values


def _get_filters():
    filters = [{'p': 'c', 't': 'countries'},
               {'p': 'g', 't': 'categories'},
               {'p': 'y', 't': 'years'},
               {'p': 'q', 't': 'rip'},
               {'p': 't', 't': 'translation'},
               ]

    return filters


def _make_filter_item(catalog, filter_id):
    url = plugin.url_for('select_filter', filter_id=filter_id, catalog=catalog, **plugin.params)
    label = _make_filter_label('yellowgreen', filter_id)
    list_item = {'label': label,
                 'is_folder': False,
                 'is_playable': False,
                 'url': url,
                 'icon': _get_filter_icon(filter_id),
                 'fanart': plugin.fanart}

    return list_item


def _get_filter_title(filter_name):
    result = ''
    if filter_name == 'categories':
        result = _('Genre')
    elif filter_name == 'years':
        result = _('Year')
    elif filter_name == 'countries':
        result = _('Country')
    elif filter_name == 'translation':
        result = _('Translation/Voice')
    elif filter_name == 'rip':
        result = _('Quality')
    #    elif filter_name =='sort': result = _('Sort')

    return result


def _get_filter_icon(filter_name):
    image = ''
    if filter_name == 'categories':
        image = plugin.get_image('DefaultGenre.png')
    elif filter_name == 'years':
        image = plugin.get_image('DefaultYear.png')
    elif filter_name == 'countries':
        image = plugin.get_image('DefaultCountry.png')
    elif filter_name == 'translation':
        image = plugin.get_image('DefaultLanguage.png')
    #    elif filter_name =='sort': image = plugin.get_image('DefaultMovieTitle.png')

    if not image:
        image = plugin.icon

    return image


def _get_filter_value(filter_id):
    filter_values = _get_catalog_filters()
    filter_items = _get_filter_values(filter_id)
    values = []

    for filter_item in filter_items:
        if filter_item['id'] in filter_values:
            values.append(filter_item['val'])

    if values:
        return ', '.join(values)
    else:
        return _('All')


def _make_filter_label(color, filter_id):
    title = _get_filter_title(filter_id)
    values = _get_filter_value(filter_id)

    return '[COLOR={0}][B]{1}:[/B] {2}[/COLOR]'.format(color, title, values)


def _get_catalog_filters():
    filter_string = plugin.params.get('filters', '')
    filter_values = filter_string.split('-') if filter_string else []

    return filter_values


def _get_keyboard_text(line='', heading='', hidden=False):
    kbd = xbmc.Keyboard(line, heading, hidden)
    kbd.doModal()
    if kbd.isConfirmed():
        return kbd.getText()


def _get_cert_path():
    return os.path.join(plugin.path, 'resources', 'cert')


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
        favorited = item.get('favorited')
        if favorited is not None:
            url = plugin.url_for('toogle_favorites', id=item['id'], value=(0 if favorited else 1))
            if item['favorited']:
                context_menu.append((_('Remove from Favorites'), 'RunPlugin({0})'.format(url)))
            else:
                context_menu.append((_('Add to Favorites'), 'RunPlugin({0})'.format(url)))

        watch_later = item.get('watch_later')
        if watch_later is not None:
            url = plugin.url_for('toogle_watch_later', id=item['id'], value=(0 if watch_later else 1))
            if item['watch_later']:
                context_menu.append((_('Remove from Watch Later'), 'RunPlugin({0})'.format(url)))
            else:
                context_menu.append((_('Add to Watch Later'), 'RunPlugin({0})'.format(url)))

    return context_menu


def _use_atl_names():
    return plugin.params.get('atl', '').lower() == 'true' \
           or plugin.get_setting('use_atl_names')


def _is_movie(content_info):
    if content_info.get('player_links') is None:
        return int(content_info['section']) in [0, 14]
    else:
        return int(content_info['section']) in [0, 14] \
               and len(content_info['player_links']['playlist']) == 0


def _add_episode_info(listitem, episode, int_season, item, use_atl_names, u_params):
    listitem['info']['video']['episode'] = int(episode)
    listitem['info']['video']['sortepisode'] = int(episode)

    url = plugin.url_for('play_video', e=episode, **u_params)
    listitem['url'] = url

    if use_atl_names:
        atl_name_parts = []
        if item.get('original_title', ''):
            series_title = item['original_title']
        else:
            series_title = item['title']
        atl_name_parts.append(series_title)

        atl_name_parts.append('.s%02de%02d' % (int_season, int(episode)))

        title = ''.join(atl_name_parts)
    else:
        title = '{0} {1}'.format(_('Episode'), episode)

    listitem['label'] = title
    listitem['info']['video']['title'] = title


@plugin.route('/openmeta/<content_type>/')
def openmeta_search(content_type):
    title = plugin.params.get('title')
    year = plugin.params.get('year')
    season = plugin.params.get('season')
    episode = plugin.params.get('episode')

    part_match = True  # (plugin.params.get('part_match') == 'true')

    try:
        api = Filmix()
        catalog_info = api.get_search_catalog(title, 1)
    except (FilmixError, simplemedia.WebClientError) as e:
        plugin.notify_error(e)
        plugin.create_directory([], succeeded=False)
    else:

        title_upper = title.upper()
        if year is not None:
            year_string = '({0})'.format(year)
            if title_upper.endswith(year_string):
                title_upper = title_upper[0:-len(year_string)].strip()

        for item in catalog_info['items']:

            if not isinstance(item, dict):
                continue

            if year is not None \
                    and not item['year'] == year:
                continue

            if not (_openmeta_compare_title(title_upper, item['title'], part_match)
                    or _openmeta_compare_title(title_upper, item['original_title'], part_match)):
                continue

            mediatype = 'movie' if _is_movie(item) else 'tvshow'

            if mediatype == 'movie' \
                    and content_type == 'movies':

                try:
                    api = Filmix()
                    content_info = api.get_movie_info(item['id'], item['alt_name'])
                except (FilmixError, simplemedia.WebClientError) as e:
                    plugin.notify_error(e)
                    plugin.create_directory([], succeeded=False)
                else:
                    result = {'items': _list_movie_files(content_info),
                              'content': 'movies',
                              }

            elif mediatype == 'tvshow' \
                    and content_type == 'tvshows':

                try:
                    api = Filmix()
                    serial_info = api.get_movie_info(item['id'], item['alt_name'])
                except (FilmixError, simplemedia.WebClientError) as e:
                    plugin.notify_error(e)
                    plugin.create_directory([], succeeded=False)
                else:

                    result = {'items': _openmeta_episodes_items(serial_info, season, episode),
                              'content': 'episodes',
                              }
            else:
                result = {'items': [],
                          'succeeded': False,
                          }

            plugin.create_directory(**result)
            break


def _openmeta_episodes_items(item, season_str, episode_str):
    listitem = _get_listitem(item)

    use_atl_names = _use_atl_names()

    listitem['is_folder'] = False
    listitem['is_playable'] = True

    int_season = max(1, int(season_str or '1'))
    int_episode = int(episode_str)

    listitem['info']['video']['season'] = int_season
    listitem['info']['video']['sortseason'] = int_season
    listitem['info']['video']['mediatype'] = 'episode'

    u_params = {'content_name': '{0}-{1}'.format(item['id'], item['alt_name']),
                'catalog': _section_catalog(item['section']),
                }

    if season_str is not None:
        u_params['s'] = season_str

    if use_atl_names:
        u_params['strm'] = 1

    for season_translation_item in _openmeta_season_translation(item, season_str):
        translation = season_translation_item[0]
        u_params['t'] = translation

        season_translation = season_translation_item[1]

        if isinstance(season_translation, list):
            for episode, episode_info in enumerate(season_translation):
                episode_num = episode + 1
                if episode_num == int_episode:
                    _add_episode_info(listitem, episode + 1, int_season, item, use_atl_names, u_params)

                    listitem['info']['label'] = '{0} {1} - {2} [{3}]'.format(_('Season'), season_str, listitem['info']['label'], translation)

                    yield listitem
        else:
            for episode_item in iteritems(season_translation):

                episode = episode_item[0]
                if episode == episode_str:
                    _add_episode_info(listitem, episode, int_season, item, use_atl_names, u_params)

                    listitem['label'] = '{0} {1} - {2} [{3}]'.format(_('Season'), season_str, listitem['label'], translation)

                    yield listitem


def _openmeta_season_translation(item, season):
    player_links = _get_player_links(item)

    if isinstance(player_links, dict):
        link_season = season or '-1'
        season_translations = player_links.get(link_season)

        for key, translation_info in iteritems(season_translations):
            yield key, translation_info
    else:
        for season_translations in player_links:
            for key, translation_info in iteritems(season_translations):
                yield key, translation_info


def _openmeta_compare_title(title, item_title, part_match):
    if not item_title:
        return False

    item_title = item_title.replace(u'\xa0', ' ').upper()

    if part_match:
        return item_title.startswith(title) or title.startswith(item_title)
    else:
        return item_title == title


def _sort_by_val(item):
    return item.get('val', '')


if __name__ == '__main__':
    plugin.run()
