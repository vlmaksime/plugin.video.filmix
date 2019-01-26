# coding: utf-8
# Module: tests

from __future__ import print_function, unicode_literals
import os
import sys
import unittest
import imp
import mock
import shutil
import xbmcaddon
import xbmc
import simpleplugin

addon_name = 'plugin.video.filmix'

cwd = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(cwd, 'config')
addon_dir = os.path.join(cwd, addon_name)

xbmcaddon.init_addon(addon_dir, config_dir, True)

# prepare search history
addon = simpleplugin.Addon()
with addon.get_storage('__history__.pcl') as storage:
    history = storage.get('history', [])
    history.insert(0, {'keyword': 'Нюхач'})
    history.insert(0, {'keyword': 'Я Легенда'})
    history.insert(0, {'keyword': 'Supernatural'})
    storage['history'] = history

xbmc._set_log_level(0)

default_script = os.path.join(addon_dir, 'default.py')

# Import our module being tested
sys.path.append(addon_dir)


def tearDownModule():
    shutil.rmtree(config_dir, True)


class PluginActionsTestCase(unittest.TestCase):

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/login'.format(addon_name), '0', ''])
    def test_00_login():
        print('# login')
        xbmc.Keyboard.strings.append('')
        xbmc.Keyboard.strings.append('')
        imp.load_source('__main__', default_script)

        xbmc.Keyboard.strings.append(os.getenv('FILMIX_LOGIN', ''))
        xbmc.Keyboard.strings.append('')
        imp.load_source('__main__', default_script)

        xbmc.Keyboard.strings.append(os.getenv('FILMIX_LOGIN', ''))
        xbmc.Keyboard.strings.append('0000000000')
        imp.load_source('__main__', default_script)

        xbmc.Keyboard.strings.append(os.getenv('FILMIX_LOGIN', ''))
        xbmc.Keyboard.strings.append(os.getenv('FILMIX_PASSWORD', ''))
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/'.format(addon_name), '1', ''])
    def test_01_root():
        print('# root')
        imp.load_source('__main__', default_script)
     
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies'.format(addon_name), '2', '?page=3'])
    def test_02_catalog():
        print('# catalog')
        imp.load_source('__main__', default_script)
    
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/2896-ya-legenda-i-am-legend-2007'.format(addon_name), '3', ''])
    def test_03_video_info_movie():
        print('# video_info_movie')
        imp.load_source('__main__', default_script)
   
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/2896-ya-legenda-i-am-legend-2007/play'.format(addon_name), '4', '?strm=1'])
    def test_04_play_video_movie():
        print('# play_video_movie')
        imp.load_source('__main__', default_script)
    
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/2896-ya-legenda-i-am-legend-2007/play'.format(addon_name), '5', '?t=%D0%94%D1%83%D0%B1%D0%BB%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D1%8B%D0%B9+%5B4%D0%9A%2C+SDR%5D'])
    def test_05_play_video_movie_translation():
        print('# play_video_movie_translation')
        imp.load_source('__main__', default_script)
    
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010'.format(addon_name), '6', ''])
    def test_06_serial_info():
        print('# serial_info')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/episodes'.format(addon_name), '7', '?s=8'])
    def test_07_serial_episodes():
        print('# serial_episodes')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/episodes'.format(addon_name), '8', '?s=8&t=LostFilm'])
    def test_08_serial_episodes_translation():
        print('# serial_episodes_translation')
        imp.load_source('__main__', default_script)
 
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/play'.format(addon_name), '9', '?e=18&s=8'])
    def test_09_play_video_serial_episodes():
        print('# play_video_serial_episodes')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/serialy/6379-smotret-onlajn-sverxestestvennoe-6-sezon-2010/play'.format(addon_name), '10', '?e=18&s=8&t=LostFilm'])
    def test_10_play_video_serial_episodes_translation():
        print('# play_video_serial_episodes_translation')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search'.format(addon_name), '11', ''])
    def test_11_search():
        print('# search')
        xbmc.Keyboard.strings.append('Смешарики')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search/history'.format(addon_name), '12', ''])
    def test_12_search_history():
        print('# search_history')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/favorites'.format(addon_name), '13', ''])
    def test_13_favourites():
        print('# favorites')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/watch_history'.format(addon_name), '14', ''])
    def test_14_watch_history():
        print('# watch_history')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/watch_later'.format(addon_name), '15', ''])
    def test_15_watch_history():
        print('# watch_later')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/popular'.format(addon_name), '16', ''])
    def test_16_popular():
        print('# popular')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/top_views'.format(addon_name), '17', ''])
    def test_17_top_views():
        print('# top_views')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/dokumentalenye/14624-skorost-zhizni-2010'.format(addon_name), '18', ''])
    def test_18_serial_seasons_without_seasons():
        print('# serial_seasons_without_seasons')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/dokumentalenye/14624-skorost-zhizni-2010/episodes'.format(addon_name), '19', ''])
    def test_19_serial_episodes_without_seasons():
        print('# serial_episodes_without_seasons')
        imp.load_source('__main__', default_script)
 
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/dokumentalenye/14624-skorost-zhizni-2010/episodes'.format(addon_name), '20', '?t=%D0%9F%D0%BB%D0%B5%D0%B5%D1%80+1'])
    def test_20_serial_episodes_without_seasons_translation():
        print('# serial_episodes_without_seasons_translation')
        imp.load_source('__main__', default_script)
  
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search'.format(addon_name), '21', '?keyword=%D0%A1%D0%BC%D0%B5%D1%88%D0%B0%D1%80%D0%B8%D0%BA%D0%B8'])
    def test_21_search_keyword():
        print('# search_keyword')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_favorites'.format(addon_name), '22', '?id=14624&value=1'])
    def test_22_add_favorite():
        print('# add_favorite')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_favorites'.format(addon_name), '23', '?id=14624&value=0'])
    def test_23_remove_favorite():
        print('# remove_favorite')
        imp.load_source('__main__', default_script)
 
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_watch_later'.format(addon_name), '24', '?id=14624&value=1'])
    def test_24_add_watch_later():
        print('# add_watch_later')
        imp.load_source('__main__', default_script)
 
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/toogle_watch_later'.format(addon_name), '25', '?id=14624&value=0'])
    def test_25_remove_watch_later():
        print('# remove_watch_later')
        imp.load_source('__main__', default_script)
 
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/movies/2896-ya-legenda-i-am-legend-2007/play'.format(addon_name), '26', ''])
    def test_26_play_trailer():
        print('# play_trailer')
        imp.load_source('__main__', default_script)
    
    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/logout'.format(addon_name), '30', ''])
    def test_30_logout():
        print('# logout')
        imp.load_source('__main__', default_script)


if __name__ == '__main__':
    unittest.main()
