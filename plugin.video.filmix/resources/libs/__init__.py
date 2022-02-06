# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import platform

import simplemedia
import xbmc
import requests

from .filmix import FilmixClient, FilmixError
from .mplay import MplayClient, MplayError

addon = simplemedia.Addon()

__all__ = ['Filmix', 'FilmixError',
           'Mplay', 'MplayError']


class FilmixWebClient(simplemedia.WebClient):

    def head(self, url, **kwargs):
        try:
            r = super(FilmixWebClient, self).head(url, **kwargs)
        except simplemedia.WebClientError as e:
            if isinstance(e.message, requests.HTTPError):
                r = e.message.response
            else:
                raise e
        return r


class Filmix(FilmixClient):

    def __init__(self):

        super(Filmix, self).__init__()

        headers = self._client.headers
        if addon.kodi_major_version() >= '17':
            headers['User-Agent'] = xbmc.getUserAgent()

        self._client = FilmixWebClient(headers)

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
