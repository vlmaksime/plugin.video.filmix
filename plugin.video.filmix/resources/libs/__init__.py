# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals
import os
import simplemedia

from .filmix import *

addon = simplemedia.Addon()


class Filmix(FilmixClient):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Filmix, cls).__new__(cls, *args, **kwargs)
            addon.log_debug('Created {0}'.format(cls._instance))
        return cls._instance

    def __init__(self):

        super(Filmix, self).__init__()

        headers = self._client.headers

        filmix_token = addon.get_setting('X-FX-Token')
        if filmix_token:
            headers['X-FX-Token'] = filmix_token

        cookie_file = self.get_cookie_path()

        new_client = simplemedia.WebClient(headers, cookie_file)
        new_client._secret_data.append('login_password')

        new_client.cert = self._client.cert
        new_client.verify = self._client.verify
        new_client.adapters = self._client.adapters

        self._client = new_client

        if addon.get_setting('user_name'):
            self.check_login()

    def check_login(self):
        try:
            user_data = self.user_data()
        except (FilmixError, simplemedia.WebClientError) as e:
            addon.notify_error(e)
        else:
            user_fields = self.get_user_fields(user_data)
            addon.set_settings(user_fields)

    @staticmethod
    def get_cookie_path():
        return os.path.join(addon.profile_dir, 'filmix.cookies')

    @staticmethod
    def get_user_fields(user_info=None):
        user_info = user_info or {}

        fields = {'user_login': user_info.get('login') or '',
                  'user_name': user_info.get('display_name') or '',
                  'is_pro': user_info.get('is_pro') or False,
                  'is_pro_plus': user_info.get('is_pro_plus') or False,
                  'pro_date': user_info.get('pro_date') or '',
                  'X-FX-Token': user_info.get('X-FX-Token') or '',
                  }
        return fields

