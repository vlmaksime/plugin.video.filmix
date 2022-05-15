# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

from future.utils import PY3

if PY3:
    from urllib.parse import urlparse
else:
    from future.backports.urllib.parse import urlparse

import requests

__all__ = ['MplayClient', 'MplayError']


class MplayError(Exception):

    def __init__(self, message, code=None):
        self.message = message
        self.code = code

        super(MplayError, self).__init__(self.message)


class MplayClient(object):
    _base_url = 'http://mplay.su/'
    _box_mac = None

    def __init__(self):

        self._client = requests.Session()

    def __del__(self):
        self._client.close()

    def _add_device_info(self, params):
        params = params or {}
        params['box_mac'] = self._box_mac

        return params

    def _get(self, url, params=None, *args, **kwargs):
        params = self._add_device_info(params)

        return self._client.get(url, params=params, *args, **kwargs)

    def _head(self, url, params=None, *args, **kwargs):
        params = self._add_device_info(params)

        return self._client.head(url, params=params, *args, **kwargs)

    @staticmethod
    def _extract_json(r):

        if not r.text:
            raise MplayError('Server sent an empty response')

        try:
            j = r.json()
        except ValueError as e:
            raise MplayError(e)

        if isinstance(j, dict) \
                and j.get('error') is not None:
            if j['error'].get('user_message') is not None:
                raise MplayError(j['error']['user_message'], j['error']['code'])
            else:
                raise MplayError(j['error']['message'], j['error']['code'])
        return j

    def _activation_url(self):
        return self._base_url + '?activation=true'

    def activation_status(self):
        url = self._base_url

        params = {'cmd': 'about'}

        r = self._get(url, params=params)
        j = self._extract_json(r)

        channels = j.get('channels')
        if channels is not None:
            activation_url = self._activation_url()
            for channel in channels:
                if channel['playlist_url'] == activation_url:
                    return False

        return True

    def activation_code_request(self):
        url = self._base_url

        params = {'activation': 'true'}

        r = self._get(url, params)
        j = self._extract_json(r)

        channels = j.get('channels')
        if channels is not None:
            activation_url = self._activation_url()
            for channel in channels:
                if channel['playlist_url'] == activation_url:
                    return channel['title']

        raise MplayError('Activation code not received')

    def get_filmix_hd_token(self):
        url = self._base_url + '?.mp4'

        params = {'cmd': 'mediateka',
                  'su': 'get',
                  'su_n': '2273e9819b547497298980075323b05b',
                  'su_str': 'Дубльований [Український]',
                  }

        r = self._head(url, params=params)
        if r.status_code not in [302]:
            raise MplayError('Filmix token don\'t receaved')

        hd_stream_url = r.headers.get('Location')
        return self.get_token_from_filmix_url(hd_stream_url)

    @staticmethod
    def get_token_from_filmix_url(stream_url):

        url_parts = urlparse(stream_url)

        if url_parts.netloc == 'mplay.su':
            raise MplayError('Filmix token don\'t receaved')

        return url_parts.path.split('/')[2]
