# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import json
import os
import platform
import sqlite3
import time

import requests
import simplemedia
import xbmc
from future.utils import PY3, iteritems

from .filmix import FilmixClient, FilmixError
from .mplay import MplayClient, MplayError

if PY3:
    from urllib.parse import urlencode, urlparse
else:
    from future.backports.urllib.parse import urlencode, urlparse

addon = simplemedia.Addon()

__all__ = ['Filmix', 'FilmixError',
           'Mplay', 'MplayError']


class WebCacheResponse(object):
    status_code = None
    text = None

    def __init__(self, data):
        self.status_code = data['status_code']
        self.text = data['text']

    def json(self):
        return json.loads(self.text)


class FilmixWebCache(object):

    def __init__(self, cache_dir, cache_duration=300):
        self._version = 1

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        self._cache_duration = cache_duration

        db_path = os.path.join(cache_dir, 'web_cache{0}.db'.format(self._version))
        db_exist = os.path.exists(db_path)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = self._dict_factory

        if not db_exist:
            self.create_database()

    def __del__(self):
        self.conn.close()

    @staticmethod
    def _dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def create_database(self):

        c = self.conn.cursor()
        # requests
        c.execute('CREATE TABLE requests (url text, params text, text text, status_code num, time num)')
        c.execute('CREATE UNIQUE INDEX requests_idx ON requests(url, params)')

        self.conn.commit()

    def get_request_details(self, url, params):
        url_parts = urlparse(url)

        if not self._is_cached_path(url_parts.path):
            return None

        sql_params = {'url': url_parts.path,
                      'params': self._get_params_str(params),
                      'time': time.time() - self._cache_duration
                      }

        c = self.conn.cursor()
        c.execute(
            'SELECT status_code, text FROM requests WHERE url = :url AND params = :params AND time >= :time LIMIT 1',
            sql_params)

        result = c.fetchone()
        if result is not None:
            return WebCacheResponse(result)

    def set_request_details(self, url, params, response):

        url_parts = urlparse(url)

        if not self._is_cached_path(url_parts.path):
            return

        sql_params = {'url': url_parts.path,
                      'params': self._get_params_str(params),
                      'status_code': response.status_code,
                      'text': response.text,
                      'time': time.time()
                      }

        c = self.conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO requests (url, params, status_code, text, time) VALUES (:url, :params, '
            ':status_code, :text, :time)',
            sql_params)

        self.conn.commit()

    @staticmethod
    def _get_params_str(params):
        if params is None:
            return ''

        params_copy = {}
        params_copy.update(params)

        for key, val in iteritems(params):
            if key.startswith('user_dev'):
                del params_copy[key]

        return urlencode(params_copy)

    @staticmethod
    def _is_cached_path(path):
        cached_paths = ['/api/v2/catalog', '/api/v2/popular', '/api/v2/top_views', '/api/v2/favourites',
                        '/api/v2/deferred', '/api/v2/history', '/api/v2/search', '/api/v2/filter_list']

        return (path in cached_paths \
            or path.startswith('/api/v2/post/'))


class FilmixWebClient(simplemedia.WebClient):
    _web_cache = None

    def __init__(self, cache_dir=None, cache_duration=300, **kwargs):
        super(FilmixWebClient, self).__init__(**kwargs)

        if cache_dir is not None:
            self._web_cache = FilmixWebCache(cache_dir, cache_duration)

    def head(self, url, **kwargs):
        try:
            r = super(FilmixWebClient, self).head(url, **kwargs)
        except simplemedia.WebClientError as e:
            if isinstance(e.message, requests.HTTPError):
                r = e.message.response
            else:
                raise e
        return r

    def get(self, url, **kwargs):

        if self._web_cache is not None:
            params = kwargs.get('params')

            r = self._web_cache.get_request_details(url, params)
            if r is not None:
                return r

        r = super(FilmixWebClient, self).get(url, **kwargs)

        if self._web_cache is not None \
                and r.status_code in [200] \
                and r.text:
            self._web_cache.set_request_details(url, params, r)

        return r


class Filmix(FilmixClient):

    def __init__(self):

        super(Filmix, self).__init__()

        headers = self._client.headers
        # if addon.kodi_major_version() >= '17':
        #     headers['User-Agent'] = xbmc.getUserAgent()

        if addon.get_setting('use_web_cache'):
            cache_dir = addon.profile_dir
            cache_duration = addon.get_setting('web_cache_duration') * 60
            self._client = FilmixWebClient(headers=headers, cache_dir=cache_dir, cache_duration=cache_duration)
        else:
            self._client = FilmixWebClient(headers=headers)

        self._user_dev_name = addon.get_setting('user_dev_name')
        self._user_dev_id = addon.get_setting('user_dev_id')
        self._user_dev_token = addon.get_setting('user_dev_token')
        self._user_dev_os = self._os_name()

        if not self._user_dev_id:
            self._user_dev_id = self.create_dev_id()
            addon.set_setting('user_dev_id', self._user_dev_id)

    def update_dev_token(self, dev_token):
        self._user_dev_token = dev_token

    def check_device(self):
        try:
            user_data = self.user_data()
        except (FilmixError, simplemedia.WebClientError) as e:
            addon.notify_error(e)
        else:
            user_fields = self.get_user_fields(user_data)
            addon.set_settings(user_fields)

    def get_user_fields(self, user_info=None):
        user_info = user_info or {}

        videoserver = user_info.get('videoserver') or 'AUTO'
        if user_info.get('available_servers') is not None:
            videoserver_label = user_info['available_servers'].get(videoserver)
        else:
            videoserver_label = ''
        videoserver = videoserver_label or videoserver

        fields = {'user_login': user_info.get('login') or '',
                  'user_name': user_info.get('display_name') or '',
                  'is_pro': user_info.get('is_pro') or False,
                  'is_pro_plus': user_info.get('is_pro_plus') or False,
                  'pro_date': user_info.get('pro_date') or '',
                  'videoserver': videoserver,
                  }

        # user_dev_name
        user_dev_name = 'Kodi {0} ({1})'.format(addon.kodi_version(), self._user_dev_id[-5:])
        fields['user_dev_name'] = user_dev_name

        return fields

    @staticmethod
    def _os_name():
        os_name = platform.system()
        if os_name == 'Linux':
            if xbmc.getCondVisibility('system.platform.android'):
                os_name = 'Android'
        else:
            os_name = '{0} {1}'.format(os_name, platform.release())

        return os_name


class Mplay(MplayClient):

    def __init__(self):

        super(Mplay, self).__init__()

        headers = self._client.headers
        if addon.kodi_major_version() >= '17':
            headers['User-Agent'] = xbmc.getUserAgent()

        self._client = simplemedia.WebClient(headers)

        self._box_mac = addon.get_setting('mplay_token')

    @staticmethod
    def create_token():
        import math
        import random

        result = ''
        charsets = '0123456789abcdef'
        while len(result) < 16:
            index = int(math.floor(random.random() * 15))
            result = result + charsets[index]
        return 'kodi' + result

    def update_box_token(self, box_mac):
        self._box_mac = box_mac
