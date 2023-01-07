# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import simplemedia
import xbmc
import xbmcgui
from future.utils import iteritems

from .listitems import FilterItem
from .utilities import Utilities
from .utilities import plugin, _
from .web import (Filmix, FilmixError)

__all__ = ['Filters']


class Filters(object):

    @classmethod
    def get_filters_items(cls, section_item):

        result = []
        if not section_item.get('use_filters', False):
            return result

        used_filters = cls._get_filters()
        for used_filter in used_filters:
            result.append(cls._make_filter_item(section_item['section'], used_filter['t']))

        return result

    @staticmethod
    def _get_filters():
        filters = [{'p': 'c', 't': 'countries'},
                   {'p': 'g', 't': 'categories'},
                   {'p': 'y', 't': 'years'},
                   {'p': 'q', 't': 'rip'},
                   {'p': 't', 't': 'vo'},
                   # {'p': 's', 't': 'sections'},
                   ]

        return filters

    @classmethod
    def select_filter(cls):
        section = plugin.params.get('section')
        filter_id = plugin.params.get('filter_id')

        section_item = Utilities.get_section_item(section)

        filter_title = cls.get_filter_title(filter_id)
        values_list = cls._get_filter_values(filter_id)
        #    values_list =  sorted(values_list, key=values_list.get)

        filter_values = cls._get_catalog_filters()

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

            url = plugin.url_for(section_item['section'], **params)
            xbmc.executebuiltin('Container.Update("%s")' % url)

    @classmethod
    def _get_filter_prefix(cls, filter_id):
        filters = cls._get_filters()
        for _filter in filters:
            if _filter['t'] == filter_id:
                return _filter['p']

    @classmethod
    def _get_filter_values(cls, filter_id):
        storage = plugin.get_mem_storage()
        filters = storage.get('filters', {})
        if filters.get(filter_id) is not None:
            return filters[filter_id]

        try:
            api = Filmix()
            result = api.get_filter(filter_id)
        except (FilmixError, simplemedia.WebClientError) as e:
            plugin.notify_error(e)
            filter_values = []
        else:
            prefix = cls._get_filter_prefix(filter_id)
            filter_values = []

            id_offset = 1 if prefix not in ['s'] else 0
            for key, val in iteritems(result):
                filter_values.append({'id': prefix + key[id_offset:],
                                      'val': '{0}'.format(val),
                                      })

            filter_values.sort(key=cls.sort_by_val)

            filters[filter_id] = filter_values
            storage['filters'] = filters

        return filter_values

    @classmethod
    def _make_filter_item(cls, section, filter_id):
        url = plugin.url_for('select_filter', filter_id=filter_id, section=section, **plugin.params)

        values = cls._get_filter_value(filter_id)
        filter_item = FilterItem(filter_id, values)
        filter_item.set_url(url)
        #
        # list_item = {'label': label,
        #              'is_folder': False,
        #              'is_playable': False,
        #              'url': url,
        #              'icon': cls._get_filter_icon(filter_id),
        #              'fanart': plugin.fanart}

        return filter_item

    @classmethod
    def _get_filter_value(cls, filter_id):
        filter_values = cls._get_catalog_filters()
        filter_items = cls._get_filter_values(filter_id)
        values = []

        for filter_item in filter_items:
            if filter_item['id'] in filter_values:
                values.append(filter_item['val'])

        if values:
            return ', '.join(values)
        else:
            return _('All')

    @staticmethod
    def _get_catalog_filters():
        filter_string = plugin.params.get('filters', '')
        filter_values = filter_string.split('-') if filter_string else []

        return filter_values

    @staticmethod
    def get_filter_title(filter_name):
        result = ''
        if filter_name == 'categories':
            result = _('Genre')
        elif filter_name == 'years':
            result = _('Year')
        elif filter_name == 'countries':
            result = _('Country')
        elif filter_name == 'vo':
            result = _('Translation/Voice')
        elif filter_name == 'rip':
            result = _('Quality')
        # elif filter_name == 'sort':
        #     result = _('Sort')

        return result

    @staticmethod
    def get_filter_icon(filter_name):
        image = ''
        if filter_name == 'categories':
            image = plugin.get_image('DefaultGenre.png')
        elif filter_name == 'years':
            image = plugin.get_image('DefaultYear.png')
        elif filter_name == 'countries':
            image = plugin.get_image('DefaultCountry.png')
        elif filter_name == 'translation':
            image = plugin.get_image('DefaultLanguage.png')
        # elif filter_name == 'sort':
        #     image = plugin.get_image('DefaultMovieTitle.png')

        if not image:
            image = plugin.icon

        return image

    @staticmethod
    def sort_by_val(item):
        return item.get('val', '')
