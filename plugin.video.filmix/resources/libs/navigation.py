# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import simplemedia
import xbmc
import xbmcplugin
from future.utils import iteritems
from simplemedia import py2_decode

from .filters import Filters
from .listitems import PostInfo, SeasonInfo, VideoInfo, EmptyListItem, ListItem, MainMenuItem
from .utilities import Utilities
from .utilities import plugin, cache, _
from .web import (Filmix, FilmixError,
                  Mplay, MplayError)


class FilmixCatalogs(object):
    @classmethod
    def root(cls):
        plugin.create_directory(cls._root_items(), content='', category=plugin.name)

    @classmethod
    def _root_items(cls):

        sections = Utilities.get_sections()
        for section_item in sections:

            if not section_item.get('visible', False):
                continue

            url = plugin.url_for(section_item['section'])

            item_info = MainMenuItem(section_item)
            item_info.set_url(url)

            yield item_info.get_item()

    @classmethod
    def catalog(cls, section):

        section_item = Utilities.get_section_item(section)

        filters = plugin.params.get('filters', '')

        page = plugin.params.get('page', '1')

        try:
            if section == 'popular':
                catalog_items = Filmix().popular(page)
            elif section == 'top_views':
                catalog_items = Filmix().top_views(page)
            elif section == 'favorites':
                catalog_items = Filmix().favourites(page)
            elif section == 'deferred':
                catalog_items = Filmix().deferred(page)
            elif section == 'history':
                catalog_items = Filmix().history(page)
            else:
                catalog_items = Filmix().catalog(page, section_item['id'], filters)
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e)
            plugin.create_directory([], succeeded=False)
        else:

            filters_items = Filters.get_filters_items(section_item)

            wm_params = {'filters': filters,
                         }

            wm_properties = {'wm_link': plugin.url_for(section_item['section'], wm_link=1, **wm_params),
                             'wm_addon': plugin.id,
                             'wm_label': section_item['label'],
                             }

            category_parts = [section_item['label'],
                              '{0} {1}'.format(_('Page'), page),
                              ]

            total_items = len(catalog_items)

            pages = Utilities.get_pages(total_items, page, section, filters=filters)

            total_items = len(catalog_items) + len(filters_items) + len(pages)

            result = {'items': cls._list_items(catalog_items, wm_properties, filters_items, pages),
                      'total_items': total_items,
                      'content': section_item['content'],
                      'category': ' / '.join(category_parts),
                      'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                      'update_listing': (page != '1'),
                      }
            plugin.create_directory(**result)

    @classmethod
    def _list_items(cls, items, wm_properties=None, filters=None, pages=None):

        filters = filters or []
        pages = pages or []

        wm_link = (plugin.params.get('wm_link') == '1')

        if not wm_link:
            for filter_item in filters:
                yield filter_item.get_item()

        properties = {}
        if wm_properties is not None:
            properties.update(wm_properties or {})

        api = Filmix()

        for item in items:

            if not isinstance(item, dict):
                continue

            post_info = cache.get_post_details(item['id'])
            if post_info is None \
                    or item['date_atom'] != post_info['date_atom']:
                post_info = api.post(item['id'])
                cache.set_post_details(item['id'], post_info)

            item_info = PostInfo(post_info)

            listitem = ListItem(item_info)

            url = cls._get_listitem_url(item_info)

            listitem.set_url(url)
            listitem.set_properties(properties)
            listitem.set_context_menu(cls._get_context_menu(item))

            yield listitem.get_item()

        if not wm_link:
            for page in pages:
                yield page

    @classmethod
    def post_seasons(cls, content_name):
        content = Utilities.get_content_params(content_name)

        try:
            content_info = Filmix().post(content['id'])
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e)
            plugin.create_directory([], succeeded=False)
        else:
            result = {'items': cls._list_serial_seasons(content_info),
                      'content': 'seasons',
                      'category': content_info['title'],
                      'sort_methods': xbmcplugin.SORT_METHOD_NONE,
                      }

            plugin.create_directory(**result)

    @classmethod
    def _list_serial_seasons(cls, item):
        use_atl_names = Utilities.use_atl_names()

        season_info = SeasonInfo(item)

        player_links = cls._get_player_links(item)

        translations = Utilities.get_tvshow_translations(player_links)

        translation = cache.get_post_translation(item['id'])
        if translation is None \
                or translations.get(translation) is None:
            translation = cls._get_default_translation(translations)

        if len(translations) > 1:
            yield cls._make_translation_item(item['id'], translation)

        translation_seasons = translations[translation]

        for season_item in translation_seasons:
            season_info.set_season_info(translation, season_item['season'], season_item['episodes'])
            url = cls._get_listitem_url(season_info, use_atl_names)
            listitem = ListItem(season_info)
            listitem.set_url(url)

            yield listitem.get_item()

    @classmethod
    def post_episodes(cls, content_name):
        content = Utilities.get_content_params(content_name)

        try:
            api = Filmix()
            serial_info = api.post(content['id'])
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e)
            plugin.create_directory([], succeeded=False)
        else:
            season = plugin.params.s
            translation = plugin.params.get('t')

            use_atl_names = Utilities.use_atl_names()
            if use_atl_names:
                sort_methods = xbmcplugin.SORT_METHOD_TITLE
            else:
                sort_methods = xbmcplugin.SORT_METHOD_EPISODE

            result = {'items': cls._list_episodes_items(serial_info, season, translation),
                      'content': 'episodes',
                      'category': ' / '.join([serial_info['title'], '{0} {1}'.format(_('Season'), season)]),
                      'sort_methods': sort_methods,
                      }

            plugin.create_directory(**result)

    @classmethod
    def _list_episodes_items(cls, item, season=None, translation=None):
        use_atl_names = Utilities.use_atl_names()

        episode_info = VideoInfo(item, atl_names=use_atl_names)

        season_translation = cls._get_season_translation(item, season, translation)

        if season_translation is not None:
            if isinstance(season_translation, list):
                for episode, episode_item in enumerate(season_translation):
                    episode_info.set_episode_info(season, episode, translation)

                    listitem = ListItem(episode_info)

                    url = cls._get_listitem_url(episode_info, use_atl_names)
                    listitem.set_url(url)

                    yield listitem.get_item()
            else:
                for episode_item in iteritems(season_translation):
                    episode = episode_item[0]
                    episode_info.set_episode_info(season, episode, translation)

                    listitem = ListItem(episode_info)

                    url = cls._get_listitem_url(episode_info, use_atl_names)
                    listitem.set_url(url)

                    yield listitem.get_item()

    @classmethod
    def play_video(cls, content_name):
        content = Utilities.get_content_params(content_name)

        succeeded = True

        try:
            post_info = Filmix().post(content['id'])
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e, True)
            succeeded = False
            listitem = EmptyListItem()
        else:

            translation = plugin.params.get('t')
            season = plugin.params.get('s')
            episode = plugin.params.get('e')

            video_item = VideoInfo(post_info, True)

            listitem = ListItem(video_item)

            if Utilities.is_movie(post_info):
                path = cls._get_movie_link(post_info, translation)
            else:
                video_item.set_episode_info(season, episode, translation)
                path = cls._get_episode_link(post_info, season, episode, translation)

            if path is None:
                plugin.resolve_url({}, False)
                return

            listitem.set_path(path)

            url = cls._get_listitem_url(video_item)
            listitem.set_url(url)

            data = {'post_id': content['id'],
                    'translation': translation,
                    'season': season,
                    'episode': episode,
                    }
            plugin.send_notification('OnPlay', data)

        if succeeded \
                and Utilities.is_strm():
            listitem.__class__ = EmptyListItem

        plugin.resolve_url(listitem.get_item(), succeeded)

    @classmethod
    def play_trailer(cls, content_name):
        content = Utilities.get_content_params(content_name)

        try:
            api = Filmix()
            content_info = api.post(content['id'])
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e)
            plugin.resolve_url({}, False)
        else:

            listitem = {'path': cls._get_trailer_link(content_info),
                        }

            plugin.resolve_url(listitem)

    @classmethod
    def _get_season_translation(cls, item, season, translation):
        player_links = cls._get_player_links(item)

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

    @classmethod
    def _get_player_links(cls, item):
        link_source = 'movie' if Utilities.is_movie(item) else 'playlist'
        return item['player_links'][link_source]

    @classmethod
    def _get_movie_link(cls, item, translation=None):
        player_links = cls._get_player_links(item)

        link_item = Utilities.get_translation_link(player_links, translation)
        if link_item is None:
            return None

        if link_item['translation'] == 'Заблокировано правообладателем!':
            plugin.notify_error(link_item['translation'], True)
            return None

        url = link_item['link']

        use_mplay = Utilities.use_mplay()
        if use_mplay:
            try:
                url = cls._replace_token(url)
            except (MplayError, simplemedia.WebClientError) as e:
                use_mplay = False
                if isinstance(e, MplayError):
                    plugin.notify_error(e)

        api = Filmix()

        sub_a = url.find('[')
        sub_b = url.find(']')
        qualities = url[sub_a + 1:sub_b].split(',')

        video_quality = plugin.get_setting('video_quality')
        quality_list = cls._available_qualities(use_mplay)

        path = None
        for i, q in enumerate(quality_list):
            if (path is None or video_quality >= i) \
                    and q in qualities:
                stream_url = url.replace(url[sub_a:sub_b + 1], q)
                if plugin.get_setting('use_http_links'):
                    stream_url = stream_url.replace('https://', 'http://')
                if api.url_available(stream_url):
                    path = stream_url

        if plugin.get_setting('use_http_links'):
            path = cls._get_http_link(path)

        return path

    @classmethod
    def _get_episode_link(cls, item, season, episode, translation=None):
        season_translation = cls._get_season_translation(item, season, translation)

        if season_translation is None:
            return None

        if isinstance(season_translation, list):
            episode_info = season_translation[int(episode)]
        else:
            episode_info = season_translation[episode]

        api = Filmix()

        url = episode_info['link']

        use_mplay = Utilities.use_mplay()
        if use_mplay:
            try:
                url = cls._replace_token(url)
            except (MplayError, simplemedia.WebClientError) as e:
                use_mplay = False
                if isinstance(e, MplayError):
                    plugin.notify_error(e)

        qualities = episode_info['qualities']

        video_quality = plugin.get_setting('video_quality')
        quality_list = cls._available_qualities(use_mplay)

        path = None
        for i, q in enumerate(quality_list):
            if (path is None or video_quality >= i) \
                    and int(q) in qualities:
                stream_url = url % q
                if plugin.get_setting('use_http_links'):
                    stream_url = stream_url.replace('https://', 'http://')
                if api.url_available(stream_url):
                    path = stream_url

        if plugin.get_setting('use_http_links'):
            path = cls._get_http_link(path)

        return path

    @classmethod
    def _get_trailer_link(cls, item):
        player_links = item['player_links'].get('trailer')

        if player_links is None \
                or len(player_links) == 0:
            return ''

        url = player_links[0]['link']

        use_mplay = Utilities.use_mplay()
        if use_mplay:
            try:
                url = cls._replace_token(url)
            except (MplayError, simplemedia.WebClientError) as e:
                use_mplay = False
                if isinstance(e, MplayError):
                    plugin.notify_error(e)

        api = Filmix()

        sub_a = url.find('[')
        sub_b = url.find(']')
        qualities = url[sub_a + 1:sub_b].split(',')

        video_quality = plugin.get_setting('video_quality')
        quality_list = cls._available_qualities(use_mplay)

        path = None
        for i, q in enumerate(quality_list):
            if (path is None or video_quality >= i) \
                    and q in qualities:
                stream_url = url.replace(url[sub_a:sub_b + 1], q)
                if plugin.get_setting('use_http_links'):
                    stream_url = stream_url.replace('https://', 'http://')
                if api.url_available(stream_url):
                    path = stream_url

        if plugin.get_setting('use_http_links'):
            path = cls._get_http_link(path)

        return path

    @classmethod
    def _get_http_link(cls, path):
        try:
            api = Filmix()
            direct_path = api.get_direct_link(path)
        except (FilmixError, simplemedia.WebClientError):
            return path
        else:
            return direct_path.replace('https://', 'http://')

    @classmethod
    def _available_qualities(cls, use_mplay=False):
        if plugin.get_setting('is_pro_plus') \
                or use_mplay:
            return ['360', '480', '720', '1080', '1440', '2160']
        elif plugin.get_setting('user_login'):
            return ['360', '480', '720']
        else:
            return ['360', '480']

    @staticmethod
    def search_history():
        result = {'items': plugin.search_history_items(),
                  'content': '',
                  'category': ' / '.join([plugin.name, _('Search')]),
                  'sort_methods': xbmcplugin.SORT_METHOD_NONE,
                  }

        plugin.create_directory(**result)

    @staticmethod
    def search_remove(index):
        plugin.search_history_remove(index)

    @staticmethod
    def search_clear():
        plugin.search_history_clear()

    @classmethod
    def search(cls):
        keyword = plugin.params.keyword or ''
        usearch = (plugin.params.usearch == 'True')

        new_search = (keyword == '')

        if not keyword:
            keyword = plugin.get_keyboard_text('', _('Search'))

        if keyword \
                and new_search \
                and not usearch:
            with plugin.get_storage('__history__.pcl') as storage:
                _history = storage.get('history', [])
                _history.insert(0, {'keyword': keyword})
                if len(_history) > plugin.get_setting('history_length'):
                    _history.pop(-1)
                storage['history'] = _history

            plugin.create_directory([], succeeded=False)

            url = plugin.url_for('search', keyword=py2_decode(keyword))
            xbmc.executebuiltin('Container.Update("%s")' % url)

        elif keyword:
            try:
                api = Filmix()
                search_items = api.search(keyword)
            except (FilmixError, simplemedia.WebClientError) as e:
                plugin.notify_error(e)
                plugin.create_directory([], succeeded=False)
            else:

                result = {'items': cls._list_items(search_items),
                          'total_items': len(search_items),
                          'content': 'movies',
                          'category': ' / '.join([_('Search'), keyword]),
                          'sort_methods': xbmcplugin.SORT_METHOD_NONE,

                          }
                plugin.create_directory(**result)

    @staticmethod
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

    @staticmethod
    def _replace_token(stream_url):
        api = Mplay()

        hd_token = api.get_filmix_hd_token()
        if hd_token:
            stream_token = api.get_token_from_filmix_url(stream_url)
            stream_url = stream_url.replace(stream_token, hd_token)

        return stream_url

    @staticmethod
    def _get_listitem_url(item_info, use_atl_names=False):

        url_params = {
            'content_name': item_info.content_name,
            'section': item_info.get_section()
        }

        if use_atl_names \
                and item_info.mediatype in ['movie', 'episode']:
            url_params['strm'] = 1
        elif use_atl_names \
                and item_info.mediatype in ['tvshow', 'season']:
            url_params['atl'] = 1

        if item_info.mediatype == 'movie':
            return plugin.url_for('play_video', **url_params)

        elif item_info.mediatype == 'episode':
            return plugin.url_for('play_video', s=item_info.get_season(), e=item_info.get_episode(),
                                  t=item_info.get_translation(), **url_params)

        elif item_info.mediatype == 'tvshow':
            return plugin.url_for('post_seasons', **url_params)

        elif item_info.mediatype == 'season':
            return plugin.url_for('post_episodes', t=item_info.get_translation(), s=item_info.get_season(),
                                  **url_params)

    @staticmethod
    def _get_default_translation(translations):
        if isinstance(translations, list):
            return translations[0]['translation']
        elif isinstance(translations, dict):
            for translation, translations_seasons in iteritems(translations):
                return translation

    @classmethod
    def _make_translation_item(cls, item_id, translation):
        url = plugin.url_for('select_translation', id=item_id, translation=translation)
        list_item = {
            'label': '[COLOR={0}][B]{1}:[/B] {2}[/COLOR]'.format('yellowgreen',
                                                                 Filters.get_filter_title('vo'),
                                                                 translation),
            'is_folder': False,
            'is_playable': False,
            'url': url,
            'properties': {'specialsort': 'top'},
            'icon': Filters.get_filter_icon('translation'),
            'fanart': plugin.fanart}

        return list_item

    @classmethod
    def select_translation(cls):

        post_id = plugin.params.id or ''
        # translation = plugin.params.translation

        post_info = cache.get_post_details(post_id)
        player_links = cls._get_player_links(post_info)

        translations_info = Utilities.get_tvshow_translations(player_links)

        translation_values = []
        translation_titles = []
        for translation, translation_info in iteritems(translations_info):

            seasons = 0
            episodes = 0
            for season_info in translation_info:
                seasons += 1
                episodes += season_info['episodes']

            translation_title = '{0} ({1}: {2}, {3}: {4})'.format(translation, _('Seasons'), seasons,
                                                                  _('Episodes'), episodes)

            translation_titles.append(translation_title)
            translation_values.append(translation)

        import xbmcgui
        selected = xbmcgui.Dialog().select('Select translation', translation_titles)
        if selected >= 0:
            cache.set_post_translation(post_id, translation_values[selected])

            item_info = PostInfo(post_info)

            url = cls._get_listitem_url(item_info)
            xbmc.executebuiltin('Container.Update("%s")' % url)
