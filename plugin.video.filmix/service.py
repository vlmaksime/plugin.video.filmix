# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible, iteritems, PY26
from resources.libs import Filmix, FilmixError
from simplemedia import py2_decode, Addon

import xbmc
import json
import simplemedia

@python_2_unicode_compatible
class FilmixMonitor(xbmc.Monitor):

    def __init__(self):

        super(FilmixMonitor, self).__init__()
        addon = Addon()
        addon.log_debug('Started {0}'.format(self))
        if not PY26:
            import ssl
            addon.log_debug('OpenSSL version: {0}'.format(ssl.OPENSSL_VERSION))

        self._settings = self._get_settings()

    def __del__(self):
        Addon().log_debug('Stoped {0}'.format(self))

    def __str__(self):
        return '<FilmixMonitor>'
        
    def onSettingsChanged(self):
        super(FilmixMonitor, self).onSettingsChanged()

        new_settings = self._get_settings()

        for key, val in iteritems(new_settings):
            if self._settings[key] != val:
                self.check_device()
                break

        self._settings.update(new_settings)

    @staticmethod
    def _get_settings():
        addon = Addon()

        settings = {'user_dev_id': addon.get_setting('user_dev_id'),
                    'user_dev_token': addon.get_setting('user_dev_token'),
                    }
        return settings
        
    def check_device(self):
        addon = Addon()
        addon.log_debug('{0}.check_device()'.format(self))

        try:
            Filmix().check_device()
        except (FilmixError, simplemedia.WebClientError) as e:
            return False
        else:
            return True

if __name__ == '__main__':

    sleep_sec = 30
    dev_check_sec = 0

    monitor = FilmixMonitor()
    while not monitor.abortRequested():

        if dev_check_sec <= 0 \
          and monitor.check_device():
            dev_check_sec = 1800

        if monitor.waitForAbort(sleep_sec):
            break

        dev_check_sec -= sleep_sec