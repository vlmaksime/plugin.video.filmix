# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from .actions import FilmixActions, MplayActions
from .filters import Filters
from .navigation import FilmixCatalogs
from .utilities import plugin

__all__ = ['plugin']


@plugin.route('/login')
def login():
    FilmixActions.login()


@plugin.route('/select_videoserver')
def select_videoserver():
    FilmixActions.select_videoserver()


@plugin.route('/check_device')
def check_device():
    FilmixActions.check_device()


@plugin.route('/toogle_favorites')
def toogle_favorites():
    FilmixActions.toogle_favorites()


@plugin.route('/toogle_watch_later')
def toogle_watch_later():
    FilmixActions.toogle_watch_later()


@plugin.route('/')
def root():
    FilmixCatalogs.root()


@plugin.route('/movies/')
def movies():
    FilmixCatalogs.catalog('movies')


@plugin.route('/serials/')
def serials():
    FilmixCatalogs.catalog('serials')


@plugin.route('/multfilms/')
def multfilms():
    FilmixCatalogs.catalog('multfilms')


@plugin.route('/multserials/')
def multserials():
    FilmixCatalogs.catalog('multserials')


@plugin.route('/popular/')
def popular():
    FilmixCatalogs.catalog('popular')


@plugin.route('/top_views/')
def top_views():
    FilmixCatalogs.catalog('top_views')


@plugin.route('/favorites/')
def favorites():
    FilmixCatalogs.catalog('favorites')


@plugin.route('/watch_later/', 'watch_later')
@plugin.route('/deferred/')
def deferred():
    FilmixCatalogs.catalog('deferred')


@plugin.route('/watch_history/', 'watch_history')
@plugin.route('/history/')
def history():
    FilmixCatalogs.catalog('history')


@plugin.route('/<section>/<content_name>', 'list_content_old')
@plugin.route('/<section>/<content_name>/')
def post_seasons(content_name, section=None):
    FilmixCatalogs.post_seasons(content_name)


@plugin.route('/<section>/<content_name>/episodes', 'post_episodes_old')
@plugin.route('/<section>/<content_name>/episodes/')
def post_episodes(section, content_name):
    FilmixCatalogs.post_episodes(content_name)


@plugin.route('/<section>/<content_name>/play', 'play_video_old')
@plugin.route('/<section>/<content_name>/play/')
def play_video(section, content_name):
    FilmixCatalogs.play_video(content_name)


@plugin.route('/<section>/<content_name>/trailer')
def play_trailer(section, content_name):
    FilmixCatalogs.play_trailer(content_name)


@plugin.route('/search/history/')
def search_history():
    FilmixCatalogs.search_history()


@plugin.route('/search')
def search():
    FilmixCatalogs.search()


@plugin.route('/select_translation')
def select_translation():
    FilmixCatalogs.select_translation()


@plugin.route('/search/remove/<int:index>')
def search_remove(index):
    plugin.search_history_remove(index)


@plugin.route('/search/clear')
def search_clear():
    plugin.search_history_clear()


@plugin.route('/select_filter')
def select_filter():
    Filters.select_filter()


@plugin.route('/mplay_activate')
def mplay_activate():
    MplayActions.activate()


@plugin.route('/mplay_enter_token')
def mplay_enter_token():
    MplayActions.enter_token()


@plugin.route('/mplay_remove_token')
def mplay_remove_token():
    MplayActions.remove_token()
