# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from future.utils import PY26
import os
import sys
import ssl
import unittest
import imp
import mock
import shutil
import xbmcaddon
import xbmc
import simpleplugin

cwd = os.path.dirname(os.path.abspath(__file__))

addon_name = 'plugin.video.filmix'
sm_name = 'script.module.simplemedia'

temp_dir = os.path.join(cwd, 'addon_data')

if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

sm_dir = os.path.join(cwd, sm_name)
sm_config_dir = os.path.join(temp_dir, sm_name)
xbmcaddon.init_addon(sm_dir, sm_config_dir)

addon_dir = os.path.join(cwd, addon_name)
addon_config_dir = os.path.join(temp_dir, addon_name)
xbmcaddon.init_addon(addon_dir, addon_config_dir, True)

run_script = lambda : imp.load_source('__main__', os.path.join(addon_dir, 'default.py'))

# Import our module being tested
sys.path.append(addon_dir)

def setUpModule():

    if not PY26:
        print('OpenSSL version: {0}'.format(ssl.OPENSSL_VERSION))

    # prepare search history
    addon = simpleplugin.Addon()
    with addon.get_storage('__history__.pcl') as storage:
        history = ['Нюхач', 'Я Легенда', 'Supernatural', 'Смешарики', 'Deadpool', 'Маша и медведь',
                   'Домики', 'Мстители', 'Stranger Things', 'Breaking Bad']
        storage['history'] = history

def tearDownModule():

    print('Removing temporary directory: {0}'.format(temp_dir))
    shutil.rmtree(temp_dir, True)


class PluginActionsTestCase(unittest.TestCase):

    def setUp(self):

        print("Running test: {0}".format(self.id().split('.')[-1]))

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/login'.format(addon_name), '0', ''])
    def test_00_login():

        login = os.getenv('FILMIX_LOGIN', None)
        password = os.getenv('FILMIX_PASSWORD', None)

        if login is None:
            login = 'login'
            print('Login not defined')

        if password is None:
            password = 'password'
            print('Password not defined')

        xbmc.Keyboard.strings.append(login)
        xbmc.Keyboard.strings.append('0000000000')
        run_script()

        xbmc.Keyboard.strings.append(login)
        xbmc.Keyboard.strings.append(password)
        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/'.format(addon_name), '1', ''])
    def test_01_root():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/'.format(addon_name), '2', '?page=3'])
    def test_02_catalog():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/2896-ya-legenda-i-am-legend-2007/'.format(addon_name), '3', ''])
    def test_03_video_info_movie():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/2896-ya-legenda-i-am-legend-2007/play/'.format(addon_name), '4', '?strm=1'])
    def test_04_play_video_movie():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/2896-ya-legenda-i-am-legend-2007/play/'.format(addon_name), '5', '?t=%D0%94%D1%83%D0%B1%D0%BB%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D1%8B%D0%B9+%5B4%D0%9A%2C+SDR%5D'])
    def test_05_play_video_movie_translation():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/'.format(addon_name), '6', ''])
    def test_06_serial_info():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/episodes/'.format(addon_name), '7', '?s=8'])
    def test_07_serial_episodes():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/episodes/'.format(addon_name), '8', '?s=8&t=LostFilm'])
    def test_08_serial_episodes_translation():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/play/'.format(addon_name), '9', '?e=18&s=8'])
    def test_09_play_video_serial_episodes():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/play/'.format(addon_name), '10', '?e=18&s=8&t=LostFilm'])
    def test_10_play_video_serial_episodes_translation():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search'.format(addon_name), '11', ''])
    def test_11_search():

        xbmc.Keyboard.strings.append('Смешарики')
        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search/history/'.format(addon_name), '12', ''])
    def test_12_search_history():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/favorites/'.format(addon_name), '13', ''])
    def test_13_favourites():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/watch_history/'.format(addon_name), '14', ''])
    def test_14_watch_history():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/watch_later/'.format(addon_name), '15', ''])
    def test_15_watch_history():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/popular/'.format(addon_name), '16', ''])
    def test_16_popular():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/top_views/'.format(addon_name), '17', ''])
    def test_17_top_views():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/dokumentalenye/14624-skorost-zhizni-2010/'.format(addon_name), '18', ''])
    def test_18_serial_seasons_without_seasons():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/dokumentalenye/14624-skorost-zhizni-2010/episodes/'.format(addon_name), '19', ''])
    def test_19_serial_episodes_without_seasons():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/dokumentalenye/14624-skorost-zhizni-2010/episodes/'.format(addon_name), '20', '?t=%D0%9F%D0%BB%D0%B5%D0%B5%D1%80+1'])
    def test_20_serial_episodes_without_seasons_translation():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search'.format(addon_name), '21', '?keyword=%D0%A1%D0%BC%D0%B5%D1%88%D0%B0%D1%80%D0%B8%D0%BA%D0%B8'])
    def test_21_search_keyword():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_favorites'.format(addon_name), '22', '?id=14624&value=1'])
    def test_22_add_favorite():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_favorites'.format(addon_name), '23', '?id=14624&value=0'])
    def test_23_remove_favorite():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_watch_later'.format(addon_name), '24', '?id=14624&value=1'])
    def test_24_add_watch_later():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_watch_later'.format(addon_name), '25', '?id=14624&value=0'])
    def test_25_remove_watch_later():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/trailer'.format(addon_name), '26', ''])
    def test_26_play_trailer():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/70388-transformery-energon-transformer-super-link-multserial-2004/'.format(addon_name), '27', ''])
    def test_27_serial_seasons_without_seasons():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search/remove/0'.format(addon_name), '28', ''])
    def test_28_search_remove():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search/clear'.format(addon_name), '29', ''])
    def test_29_search_clear():

        run_script()

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/logout'.format(addon_name), '30', ''])
    def test_30_logout():

        run_script()


if __name__ == '__main__':
    unittest.main()
