# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import simplemedia
import xbmcgui
from future.utils import iteritems
from simplemedia import py2_decode, WebClientError

plugin = simplemedia.RoutedPlugin()
_ = plugin.initialize_gettext()

__all__ = ['plugin', 'py2_decode', '_', 'WebClientError', 'Utilities']


class Utilities(object):

    @classmethod
    def get_sections(cls):
        movie_icon = plugin.get_image('DefaultMovies.png')
        tvshow_icon = plugin.get_image('DefaultTVShows.png')
        favour_icon = plugin.get_image('DefaultFavourites.png')
        search_icon = plugin.get_image('DefaultAddonsSearch.png')

        user_logged = (plugin.get_setting('user_login') != '')
        use_filters = plugin.get_setting('use_filters')

        s = [  # Main Sections
            cls._create_section_item('movies', _('Movies'), movie_icon, 'movies', section_id='999',
                                     use_filters=use_filters),
            cls._create_section_item('serials', _('TV Series'), tvshow_icon, 'tvshows', section_id='7',
                                     use_filters=use_filters),
            cls._create_section_item('multfilms', _('Cartoons'), movie_icon, 'movies', section_id='14',
                                     use_filters=use_filters),
            cls._create_section_item('multserials', _('Cartoon Series'), tvshow_icon, 'tvshows', section_id='93',
                                     use_filters=use_filters),
            # Popular
            cls._create_section_item('popular', _('Popular'), movie_icon, 'movies'),
            # Top Views
            cls._create_section_item('top_views', _('Top Views'), movie_icon, 'movies'),
            # Favorites
            cls._create_section_item('favorites', _('Favorites'), favour_icon, 'movies', visible=user_logged),
            # Watch Later
            cls._create_section_item('deferred', _('Watch Later'), favour_icon, 'movies', visible=user_logged),
            # Watch History
            cls._create_section_item('history', _('Watch History'), movie_icon, 'movies', visible=user_logged),
            # Search
            cls._create_section_item('search_history', _('Search'), search_icon, ''),
        ]

        return s

    @staticmethod
    def _create_section_item(section, label, icon, content, section_id=None, visible=True, use_filters=False):
        section_item = {'section': section,
                        'label': label,
                        'id': section_id,
                        'is_section': (section_id is not None),
                        'icon': icon,
                        'content': content,
                        'visible': visible,
                        'use_filters': use_filters
                        }

        return section_item

    @classmethod
    def get_section_item(cls, section):
        sections = cls.get_sections()
        for item in sections:
            if item['section'] == section:
                return item

    @classmethod
    def get_section_item_by_id(cls, section_id):
        sections = cls.get_sections()
        for item in sections:
            if item['is_section'] \
                    and item['id'] == section_id:
                return item

    @classmethod
    def get_content_params(cls, content_name):
        sep = content_name.find('-')

        result = {'id': content_name[:sep],
                  'alt_name': content_name[sep + 1:],
                  }

        return result

    @classmethod
    def get_pages(cls, total_items, page, section, **kwargs):
        per_page = 50

        if not isinstance(page, int):
            page = int(page)

        page_params = kwargs or {}

        pages = []
        if page > 1:
            if page == 2:
                url = plugin.url_for(section, **page_params)
            else:
                url = plugin.url_for(section, page=(page - 1), **page_params)
            item_info = {'label': _('Previous page...'),
                         'url': url}
            pages.append(item_info)

        if per_page <= total_items:
            url = plugin.url_for(section, page=(page + 1), **page_params)
            item_info = {'label': _('Next page...'),
                         'url': url}
            pages.append(item_info)

        return pages

    @classmethod
    def get_translation_link(cls, player_links, translation=None):
        if len(player_links) == 1:
            return player_links[0]

        translations = []

        for link_item in player_links:
            if link_item['translation'] == translation:
                return link_item

            link_qualities = cls.get_link_qualities(link_item['link'])

            translation_title = '{0} [{1}]'.format(link_item['translation'], link_qualities[0])

            translations.append(translation_title)

        selected = xbmcgui.Dialog().select('Select translation', translations)

        if selected >= 0:
            return player_links[selected]

    @classmethod
    def get_link_qualities(cls, link):
        sub_a = link.find('[')
        sub_b = link.find(']')
        qualities = link[sub_a + 1:sub_b].split(',')

        return [quality for quality in qualities if quality != '']

    @staticmethod
    def get_tvshow_translations(player_links):

        if isinstance(player_links, dict):

            translations = {}

            for season, season_translations in iteritems(player_links):
                for translation, playlist in iteritems(season_translations):
                    translation_seasons = translations.get(translation, [])
                    season_info = {'season': season,
                                   'episodes': len(playlist)}
                    translation_seasons.append(season_info)

                    translations[translation] = translation_seasons

            return translations

    @staticmethod
    def get_filter_title(filter_name):
        from .filters import Filters
        return Filters.get_filter_title(filter_name)

    @staticmethod
    def get_filter_icon(filter_name):
        from .filters import Filters
        return Filters.get_filter_icon(filter_name)

    @staticmethod
    def use_mplay():
        use_mplay = (plugin.get_setting('use_mplay_token')
                     and plugin.get_setting('mplay_token') != '')
        return use_mplay

    @staticmethod
    def use_atl_names():
        return plugin.params.get('atl', '').lower() == 'true' \
               or plugin.get_setting('use_atl_names')

    @staticmethod
    def is_strm():
        is_strm = plugin.params.get('strm') == '1' \
                  and plugin.kodi_major_version() >= '18'
        return is_strm

    @staticmethod
    def is_movie(content_info):
        if content_info.get('player_links') is None:
            return int(content_info['section']) in [0, 14]
        else:
            return len(content_info['player_links']['movie']) != 0

