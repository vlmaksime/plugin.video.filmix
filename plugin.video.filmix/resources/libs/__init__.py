# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals
import os
import xbmc
import platform
import simplemedia

from .filmix import *

addon = simplemedia.Addon()


class Filmix(FilmixClient):

    def __init__(self):

        super(Filmix, self).__init__()

        headers = self._client.headers

        new_client = simplemedia.WebClient(headers)
        new_client._secret_data.append('login_password')

        new_client.cert = self._client.cert
        new_client.verify = self._client.verify
        new_client.adapters = self._client.adapters

        self._client = new_client

        os_name = platform.system()
        if os_name == 'Linux':
            if xbmc.getCondVisibility('system.platform.android'):
                os_name = 'Android'
        else:
            os_name = '{0} {1}'.format(os_name, platform.release())

        self._user_dev_name = 'Kodi {0} ({1})'.format(addon.kodi_version(), os_name)
        self._user_dev_id = addon.get_setting('user_dev_id')
        self._user_dev_token = addon.get_setting('user_dev_token')

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

    @staticmethod
    def get_user_fields(user_info=None):
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
        return fields

