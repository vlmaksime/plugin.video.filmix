# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import simplemedia
import xbmc
import xbmcgui
from future.utils import iteritems

from .utilities import plugin, WebClientError, _
from .web import Filmix, FilmixError


class FilmixActions(object):
    @staticmethod
    def login():
        try:
            api = Filmix()
            token_result = api.token_request()
            update_info = api.check_update()
        except (FilmixError, WebClientError) as e:
            plugin.notify_error(e, True)
        else:
            api.update_dev_token(token_result['code'])
            plugin.set_setting('user_dev_token', token_result['code'])

            code = token_result['user_code']
            domain = update_info['domain']

            progress = plugin.dialog_progress_create(_('Authorization'),
                                                     _('Connection code: [B]{0}[/B]').format(code),
                                                     _('Enter code on the page [B]{0}/consoles[/B]').format(domain),
                                                     _('or in the site menu [B]\'Profile\' -> \'Consoles\'[/B]'))
            wait_sec = 300
            step_sec = 2
            pass_sec = 0
            check_sec = 20

            user_fields = api.get_user_fields()
            while pass_sec < wait_sec:
                if progress.iscanceled():
                    return

                xbmc.sleep(step_sec * 1000)
                pass_sec += step_sec

                plugin.dialog_progress_update(progress, int(100 * pass_sec / wait_sec))

                if (pass_sec % check_sec) == 0:
                    try:
                        user_data = api.user_data()
                    except (FilmixError, WebClientError) as e:
                        plugin.notify_error(e)
                    else:
                        user_fields = api.get_user_fields(user_data)
                        if user_fields['user_login']:
                            break

            progress.close()

            plugin.set_settings(user_fields)

            if user_fields['user_login']:
                plugin.dialog_ok(_('You have successfully logged in'))
            else:
                plugin.dialog_ok(_('Login failure! Please, try later'))

    @staticmethod
    def select_videoserver():
        api = Filmix()
        try:
            user_data = api.user_data()
        except (FilmixError, WebClientError) as e:
            plugin.notify_error(e)
        else:
            keys = []
            titles = []
            for key, val in iteritems(user_data.get('available_servers')):
                titles.append(val)
                keys.append(key)

            videoserver = user_data.get('videoserver') or 'AUTO'

            if titles:
                if plugin.kodi_major_version() >= '17':
                    preselect = keys.index(videoserver)
                    selected = xbmcgui.Dialog().select(_('Select video server'), titles, preselect=preselect)
                else:
                    selected = xbmcgui.Dialog().select(_('Select video server'), titles)

                if selected is not None \
                        and keys[selected] != videoserver:
                    try:
                        result = api.set_videoserver(keys[selected])
                    except (FilmixError, WebClientError) as e:
                        plugin.notify_error(e)
                    else:
                        if result['status'] == 'ok' \
                                and videoserver != result['server']:
                            plugin.set_setting('videoserver', user_data['available_servers'].get(result['server']))
                            xbmcgui.Dialog().notification(plugin.name, _('Video server successfully changed'),
                                                          xbmcgui.NOTIFICATION_INFO)

    @staticmethod
    def check_device():
        Filmix().check_device()

    @staticmethod
    def toogle_favorites():
        content_id = plugin.params.get('id')

        try:
            api = Filmix()
            result = api.set_favorite(content_id)
        except (FilmixError, WebClientError) as e:
            plugin.notify_error(e, True)
        else:
            if result.get('id') is not None:
                xbmcgui.Dialog().notification(plugin.name, _('Successfully added to Favorites'),
                                              xbmcgui.NOTIFICATION_INFO)
            else:
                xbmcgui.Dialog().notification(plugin.name, _('Successfully removed from Favorites'),
                                              xbmcgui.NOTIFICATION_INFO)

            xbmc.executebuiltin('Container.Refresh()')

    @staticmethod
    def toogle_watch_later():
        content_id = plugin.params.get('id')

        try:
            api = Filmix()
            result = api.set_watch_later(content_id)
        except (FilmixError, WebClientError) as e:
            plugin.notify_error(e, True)
        else:
            if result.get('id') is not None:
                xbmcgui.Dialog().notification(plugin.name, _('Successfully added to Watch Later'),
                                              xbmcgui.NOTIFICATION_INFO)
            else:
                xbmcgui.Dialog().notification(plugin.name, _('Successfully removed from Watch Later'),
                                              xbmcgui.NOTIFICATION_INFO)

            xbmc.executebuiltin('Container.Refresh()')


