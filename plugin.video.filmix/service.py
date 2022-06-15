# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import json

import simplemedia
import xbmc
from future.utils import python_2_unicode_compatible, iteritems
from simplemedia import py2_decode, Addon

from resources.libs.web import Filmix, FilmixError


@python_2_unicode_compatible
class FilmixMonitor(xbmc.Monitor):

    def __init__(self):

        super(FilmixMonitor, self).__init__()
        addon = Addon()
        addon.log_debug('Started {0}'.format(self))

        self._settings = self._get_settings()

    def __del__(self):
        Addon().log_debug('Stopped {0}'.format(self))

    def __str__(self):
        return '<FilmixMonitor>'

    def onNotification(self, sender, method, data):
        super(FilmixMonitor, self).onNotification(sender, method, data)

        addon = Addon()
        addon.log_debug('{0}.onNotification({1}, {2}, {3})'.format(self, sender, method, py2_decode(data)))

        if sender == addon.id:
            if method == 'Other.OnPlay':
                if data != 'nill':
                    data = json.loads(data)
                    try:
                        Filmix().add_watched(**data)
                    except (FilmixError, simplemedia.WebClientError) as e:
                        addon.log_error('{0}'.format(e))

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
        except (FilmixError, simplemedia.WebClientError):
            return False
        else:
            return True


def run():
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


if __name__ == '__main__':
    run()
