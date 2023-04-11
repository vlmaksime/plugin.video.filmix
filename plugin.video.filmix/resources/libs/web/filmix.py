# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import requests

__all__ = ['FilmixClient', 'FilmixError']


class FilmixError(Exception):

    def __init__(self, message, code=None):
        self.message = message
        self.code = code

        super(FilmixError, self).__init__(self.message)


class FilmixClient(object):
    _base_url = 'http://filmixapp.cyou/'

    _user_dev_apk = '2.0.9'
    _user_dev_id = None
    _user_dev_name = None
    _user_dev_token = None
    _user_dev_vendor = None
    _user_dev_os = None

    def __init__(self, api_url=''):

        if api_url:
            self._base_url = api_url

        headers = {#'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Accept-Encoding': 'gzip',
                   'Content-Length': '0',
                   'Accept': None,
                   'User-Agent': None
                   }

        self._client = requests.Session()
        self._client.headers.update(headers)

    def __del__(self):
        self._client.close()

    def _add_device_info(self, params):
        params = params or {}
        params['user_dev_id'] = self._user_dev_id
        params['user_dev_name'] = self._user_dev_name
        params['user_dev_token'] = self._user_dev_token
        params['user_dev_vendor'] = self._user_dev_vendor
        params['user_dev_os'] = self._user_dev_os
        params['user_dev_apk'] = self._user_dev_apk

        return params

    def _get(self, url, params=None, *args, **kwargs):
        params = self._add_device_info(params)

        return self._client.get(url, params=params, *args, **kwargs)

    def _post(self, url, data=None, *args, **kwargs):
        data = self._add_device_info(data)

        return self._client.post(url, data=data, *args, **kwargs)

    @staticmethod
    def _extract_json(r):

        if not r.text:
            raise FilmixError('Server sent an empty response')

        try:
            j = r.json()
        except ValueError as e:
            raise FilmixError(e)

        if isinstance(j, dict) \
                and j.get('error') is not None:
            if j['error'].get('user_message') is not None:
                raise FilmixError(j['error']['user_message'], j['error']['code'])
            else:
                raise FilmixError(j['error']['message'], j['error']['code'])
        return j

    @staticmethod
    def create_dev_id():
        import math
        import random

        result = ''
        charsets = '0123456789abcdef'
        while len(result) < 16:
            index = int(math.floor(random.random() * 15))
            result = result + charsets[index]
        return result

    def token_request(self):
        url = self._base_url + 'api/v2/token_request'

        r = self._get(url)
        j = self._extract_json(r)

        return j

    def set_videoserver(self, vs_schg):
        url = self._base_url + '/api/v2/change_server'

        data = {'vs_schg': vs_schg,
                }

        r = self._post(url, data=data)
        j = self._extract_json(r)

        return j

    def user_data(self):
        url = self._base_url + 'api/v2/user_profile'

        r = self._get(url)
        j = self._extract_json(r)

        if isinstance(j, dict):
            result = j.get('user_data', {})
        else:
            result = {}

        return result

    def _get_items(self, url, u_params=None, page=1, page_params=None):
        per_page = 48

        r = self._get(url, params=u_params)
        j = self._extract_json(r) or []

        if page_params is not None:
            pages = {'prev': {'page': page - 1} if page > 1 else None,
                     'next': {'page': page + 1} if int(per_page) <= len(j) else None,
                     }
            if pages['prev'] is not None:
                pages['prev'].update(page_params)
            if pages['next'] is not None:
                pages['next'].update(page_params)
        else:
            pages = {'prev': None,
                     'next': None,
                     }

        result = {'count': len(j),
                  'items': j,
                  'pages': pages,
                  }

        return result

    def catalog(self, page=1, section=0, filters='', orderby='date', orderdir='desc'):
        url = self._base_url + 'api/v2/catalog'

        filter_items = filters.split('-') if filters else []
        filter_items.append('s{0}'.format(section))

        params = {'orderby': orderby,
                  'orderdir': orderdir,
                  'filter': '{0}'.format('-'.join(filter_items)),
                  'page': page,
                  }

        r = self._get(url, params)
        j = self._extract_json(r)

        return j

    def popular(self, page=1):
        url = self._base_url + 'api/v2/popular'

        params = {'page': page,
                  }

        r = self._get(url, params)
        j = self._extract_json(r)

        return j

    def top_views(self, page=1):
        url = self._base_url + 'api/v2/top_views'

        params = {'page': page,
                  }

        r = self._get(url, params)
        j = self._extract_json(r)

        return j

    def favourites(self, page=1, orderby='date', orderdir='desc'):
        url = self._base_url + 'api/v2/favourites'

        params = {'orderby': orderby,
                  'orderdir': orderdir,
                  'page': page,
                  }

        r = self._get(url, params)
        j = self._extract_json(r)

        return j

    def deferred(self, page=1):
        url = self._base_url + 'api/v2/deferred'

        params = {'page': page,
                  }

        r = self._get(url, params)
        j = self._extract_json(r)

        return j

    def history(self, page=1):
        url = self._base_url + 'api/v2/history'

        params = {'page': page,
                  }

        r = self._get(url, params)
        j = self._extract_json(r)

        return j

    def post(self, post_id=''):
        url = self._base_url + 'api/v2/post/{0}'.format(post_id)

        r = self._get(url)
        j = self._extract_json(r)

        return j

    def search(self, story):
        url = self._base_url + 'api/v2/search'
        params = {'story': story,
                  }

        r = self._get(url, params)
        j = self._extract_json(r)

        return j

    def get_filter(self, filter_id=None):
        url = self._base_url + 'api/v2/filter_list'

        if filter_id == 'rip':
            return self._filters_rip()

        r = self._get(url)
        j = self._extract_json(r)

        if filter_id is not None:
            return j[filter_id]
        else:
            j['rip'] = self._filters_rip()
            return j

    def set_favorite(self, post_id):
        url = self._base_url + 'api/v2/toggle_fav/{0}'.format(post_id)

        r = self._get(url)
        j = self._extract_json(r)

        return j

    def set_watch_later(self, post_id):
        url = self._base_url + 'api/v2/toggle_wl/{0}'.format(post_id)

        r = self._get(url)
        j = self._extract_json(r)

        return j

    def add_watched(self, post_id, season=None, episode=None, translation=None):
        url = self._base_url + 'api/v2/add_watched'

        data = {'add_watched': 'true',
                'id': post_id,
                }

        if season is not None:
            data['season'] = season

        if episode is not None:
            data['episode'] = episode

        if translation is not None:
            data['translation'] = translation

        self._post(url, data=data)

    def check_update(self):
        url = self._base_url + 'api/v2/check_update'

        r = self._get(url)
        return self._extract_json(r)

    def url_available(self, url):
        try:
            r = self._client.head(url)
        except:
            return True
        else:
            return r.status_code not in [403, 404]

    def get_direct_link(self, url):
        try:
            r = self._client.head(url, allow_redirects=True)
        except:
            return url
        else:
            return r.url

    @staticmethod
    def _filters_rip():
        result = {
            'fb': 'Плохое (CAM, TS)',
            'fn': 'Хорошее (DVDRip, HDRip, SAT...)',
            'fg': 'Отличное (HD 720)',
            'fh': 'Шедевральное (FHD 1080)',
            'f2': '1080p+ (FHD Ultra+)',
            'f4': '4К (UHD 2160р)'
        }

        return result
